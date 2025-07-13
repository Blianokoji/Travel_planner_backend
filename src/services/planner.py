import google.generativeai as genai
import googlemaps
import logging
import json
from typing import Dict
import re
class TravelPlanner:
    def __init__(self, gemini_api_key: str, google_maps_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.google_maps_api_key = google_maps_api_key
        
        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')

        # Configure Google Maps client
        self.gmaps = googlemaps.Client(key=self.google_maps_api_key)

    def get_location_details_and_places(self, destination: str) -> Dict:
        """
        Uses Google Places API to get:
        - Location metadata (lat/lng/address)
        - Nearby restaurants and tourist attractions with price and ratings
        """
        try:
            # Step 1: Get place info from text search
            places_result = self.gmaps.places(query=destination)
            if not places_result.get("results"):
                return {"error": f"No results found for destination: {destination}"}

            place = places_result["results"][0]
            location = place["geometry"]["location"]
            formatted_address = place.get("formatted_address", "Unknown address")

            # Step 2: Get nearby restaurants
            restaurants = self.gmaps.places_nearby(
                location=(location["lat"], location["lng"]),
                radius=5000,  # 5km
                type="restaurant"
            )

            restaurant_list = []
            for r in restaurants.get("results", [])[:10]:  # limit to 10
                restaurant_list.append({
                    "name": r.get("name", "Unknown"),
                    "address": r.get("vicinity", "Unknown"),
                    "rating": r.get("rating", "N/A"),
                    "price_level": r.get("price_level", "N/A")
                })

            # Step 3: Get nearby tourist attractions
            attractions = self.gmaps.places_nearby(
                location=(location["lat"], location["lng"]),
                radius=5000,
                type="tourist_attraction"
            )

            attraction_list = []
            for a in attractions.get("results", [])[:10]:
                attraction_list.append({
                    "name": a.get("name", "Unknown"),
                    "address": a.get("vicinity", "Unknown"),
                    "rating": a.get("rating", "N/A"),
                    "price_level": a.get("price_level", "N/A")
                })

            return {
                "location": {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "address": formatted_address
                },
                "restaurants": restaurant_list,
                "attractions": attraction_list
            }

        except Exception as e:
            logging.error(f"Error fetching location or places info: {e}")
            return {"error": f"Failed to fetch location data: {str(e)}"}

    def generate_travel_plan(self, destination: str, start_date: str, end_date: str, budget: str, preferences: str = "") -> Dict:
        """
        Generates a travel plan using Gemini API based on user input and enriched location data.
        Returns a structured JSON object: { title: str, budget: float, days: list, notes: list }
        """
        try:
            location_data = self.get_location_details_and_places(destination)
            if "error" in location_data:
                return {
                    "title": "Error",
                    "budget": 0,
                    "days": [],
                    "notes": [f"Error: {location_data['error']}"]
                }

            address_info = f" (Address: {location_data['location']['address']})"

            attractions_info = ""
            restaurants_info = ""

            if location_data.get("attractions"):
                attractions_info = "\nNearby tourist attractions:\n" + "\n".join([
                    f"- {a['name']} ({a['address']}, Rating: {a.get('rating', 'N/A')}, Price Level: {a.get('price_level', 'N/A')})"
                    for a in location_data['attractions']
                ])
            if location_data.get("restaurants"):
                restaurants_info = "\nNearby restaurants:\n" + "\n".join([
                    f"- {r['name']} ({r['address']}, Rating: {r.get('rating', 'N/A')}, Price Level: {r.get('price_level', 'N/A')})"
                    for r in location_data['restaurants']
                ])

            # Final prompt
            prompt = (
                f"Create a detailed travel itinerary for a trip to {destination}{address_info}.\n"
                f"Dates: {start_date} to {end_date}\n"
                f"Budget: {budget} in Indian Rupees\n"
                f"Preferences: {preferences if preferences else 'None'}\n\n"
                f"{attractions_info}\n"
                f"{restaurants_info}\n\n"
                f"Respond with a JSON object containing: "
                f"title (string), budget (number), days (array of objects with date and activities), "
                f"and notes (array of strings). Example:\n"
                f'{{"title": "Trip to {destination}", "budget": {budget}, "days": [{{"date": "{start_date}", "activities": [{{"time": "Morning", "description": "..."}}], ...], "notes": ["..."]}}'
            )

            logging.info(f"Sending prompt to Gemini: {prompt}")
            response = self.model.generate_content(prompt)

            if response and hasattr(response, "text"):
                raw_text = response.text.strip()
                logging.debug(f"Raw Gemini response: {raw_text}")

                # Remove markdown wrappers
                cleaned_text = re.sub(r"^```(?:json)?\s*|```$", "", raw_text, flags=re.IGNORECASE | re.MULTILINE).strip()

                try:
                    parsed = json.loads(cleaned_text)
                    # Validate structure
                    if (
                        not isinstance(parsed, dict) or
                        not isinstance(parsed.get("title"), str) or
                        not isinstance(parsed.get("budget"), (int, float)) or
                        not isinstance(parsed.get("days"), list) or
                        not all(
                            isinstance(day, dict) and
                            isinstance(day.get("date"), str) and
                            isinstance(day.get("activities"), list) and
                            all(
                                isinstance(act, dict) and
                                isinstance(act.get("time"), str) and
                                isinstance(act.get("description"), str)
                                for act in day.get("activities", [])
                            )
                            for day in parsed.get("days", [])
                        ) or
                        not isinstance(parsed.get("notes"), list) or
                        not all(isinstance(note, str) for note in parsed.get("notes", []))
                    ):
                        logging.error(f"Invalid plan structure: {parsed}")
                        return {
                            "title": "Error",
                            "budget": 0,
                            "days": [],
                            "notes": ["Error: Invalid response format from Gemini"]
                        }
                    return parsed
                except json.JSONDecodeError as decode_err:
                    logging.error(f"Failed to parse JSON from Gemini response: {decode_err}")
                    return {
                        "title": "Error",
                        "budget": 0,
                        "days": [],
                        "notes": [f"Error: Invalid JSON from Gemini: {cleaned_text}"]
                    }
            else:
                logging.error("No valid response from Gemini")
                return {
                    "title": "Error",
                    "budget": 0,
                    "days": [],
                    "notes": ["Error: No response from Gemini"]
                }

        except Exception as e:
            logging.error(f"Plan generation error: {str(e)}")
            return {
                "title": "Error",
                "budget": 0,
                "days": [],
                "notes": [f"Error: Plan generation failed: {str(e)}"]
            }