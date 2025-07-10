import google.generativeai as genai
import googlemaps
import logging
import json
from typing import Union
import re
class TravelPlanner:
    def __init__(self, gemini_api_key: str, google_maps_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.google_maps_api_key = google_maps_api_key
        
        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)
        # for m in genai.list_models():
        #     print(m.name, " — ", m.supported_generation_methods) # just so that i can list the models

        self.model = genai.GenerativeModel(model_name='gemini-2.5-pro-preview-03-25')

        # Configure Google Maps client
        self.gmaps = googlemaps.Client(key=self.google_maps_api_key)

    def get_location_details_and_places(self, destination: str):
        """
        Uses Google Places API to get:
        - Location metadata (lat/lng/address)
        - Nearby restaurants and tourist attractions with price and ratings
        """
        try:
            # Step 1: Get place info from text search
            places_result = self.gmaps.places(query=destination)
            if not places_result.get("results"):
                return None

            place = places_result["results"][0]
            location = place["geometry"]["location"]
            formatted_address = place.get("formatted_address")

            # Step 2: Get nearby restaurants
            restaurants = self.gmaps.places_nearby(
                location=(location["lat"], location["lng"]),
                radius=5000,  # 5km
                type="restaurant"
            )

            restaurant_list = []
            for r in restaurants.get("results", [])[:10]:  # limit to 10
                restaurant_list.append({
                    "name": r.get("name"),
                    "address": r.get("vicinity"),
                    "rating": r.get("rating"),
                    "price_level": r.get("price_level")  # 0 (free) to 4 (very expensive)
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
                    "name": a.get("name"),
                    "address": a.get("vicinity"),
                    "rating": a.get("rating"),
                    "price_level": a.get("price_level")
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
            return None




    def generate_travel_plan(self, destination: str, start_date: str, end_date: str, budget: str, preferences: str = "") -> Union[dict, None]:
        """
        Generates a travel plan using Gemini API based on user input and enriched location data.
        Returns a dictionary with {"plan": <string>} or None on error.
        """
        try:
            location_data = self.get_location_details_and_places(destination)
            address_info = f" (Address: {location_data['location']['address']})" if location_data else ""

            attractions_info = ""
            restaurants_info = ""

            if location_data:
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
                f"Respond ONLY with raw JSON. DO NOT include markdown or ```json. Just return:\n"
                f'{{ "plan": "your travel itinerary as a string" }}\n'
            )

            logging.info(f"Sending prompt to Gemini: {prompt}")
            response = self.model.generate_content(prompt)

            if response and hasattr(response, "text"):
                raw_text = response.text.strip()

                # Remove markdown wrappers
                cleaned_text = re.sub(r"^```(?:json)?\s*|```$", "", raw_text, flags=re.IGNORECASE | re.MULTILINE).strip()

                try:
                    parsed = json.loads(cleaned_text)
                    if isinstance(parsed.get("plan"), dict) and "plan" in parsed["plan"]:
                        parsed = { "plan": parsed["plan"]["plan"] }

                    # Ensure final output is valid
                    if "plan" in parsed and isinstance(parsed["plan"], str):
                        return parsed

                    logging.error(f"Unexpected plan format: {parsed}")
                    return {"error": "Invalid 'plan' format", "raw_response": parsed}

                except json.JSONDecodeError as decode_err:
                    logging.error(f"Failed to parse JSON from Gemini response: {decode_err}")
                    logging.debug(f"Raw Gemini response was: {cleaned_text}")
                    return {"error": "Invalid JSON", "raw_response": cleaned_text}

            return None

        except Exception as e:
            logging.error(f"Plan generation error: {str(e)}")
            return None

