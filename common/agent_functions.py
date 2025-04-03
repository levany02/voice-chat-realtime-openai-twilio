import os

import json
from datetime import datetime, timedelta
import asyncio

from openai import OpenAI
from dotenv import load_dotenv

from .retrieval_data import IMPROVE_TIME_TABLE, UPSALE_SERVICE, TIME_TABLE



load_dotenv()


async def is_available(params):
    try:
        date = params.get('date', "").title()
        name = params.get('name', "").title()
        service = params.get('service', "").title()

        time_table = IMPROVE_TIME_TABLE.get(service.title(), TIME_TABLE)

        if date == 'Tomorrow':
            date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%A")
        elif date == 'Today':
            date = datetime.date.today().strftime("%A")

        if not name and not date:
            name = next(iter(time_table), "")

        valid_days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}

        if name and name not in time_table and date not in valid_days:
            available_therapists = ", ".join(time_table.keys())
            return json.dumps({
                "check": f"{name} is not available. Available therapists: {available_therapists}. Please provide a specific day."
            })

        if name and name not in time_table and date in valid_days:
            available_therapists = [n for n, schedule in time_table.items() if schedule.get(date) != "Off"]
            if available_therapists:
                return json.dumps({
                    "check": f"Available therapists on {date}: {', '.join(available_therapists)}"
                })
            return json.dumps({"check": "No available therapists on that day."})

        if not name and date in valid_days:
            for therapist, schedule in time_table.items():
                if schedule.get(date) and schedule[date] != "Off":
                    return json.dumps({
                        "check": f"{therapist} is available from {schedule[date]} on {date}."
                    })

        if name and date not in valid_days:
            for available_date, available_time in time_table[name].items():
                if available_time != "Off":
                    return json.dumps({
                        "check": f"{name} is available from {available_time} on {available_date}."
                    })

        if time_table[name].get(date) and time_table[name][date] != "Off":
            return json.dumps({
                "check": f"{name} is available from {time_table[name][date]} on {date}."
            })
        
        other_dates = [f"{name} is available on {d} from {t}" for d, t in time_table[name].items() if t != "Off"]
        other_therapists = [f"{n} is available on {date} from {time_table[n][date]}" for n in time_table if time_table[n].get(date) and time_table[n][date] != "Off"]
        
        return json.dumps({
            "check": f"{name} is off on {date}. Available options: {', '.join(other_dates)}. Or consider {', '.join(other_therapists)}."
        })
    
    except Exception as err:
        print("Error:", err)
        return json.dumps({"check": "An error occurred while processing the request."})


async def find_nearest_location(params):
    try:
        client = OpenAI(api_key=os.getenv('OPENAPI_KEY'))
        location = params.get('address')
        if not location:
            return {
                "nearest_location": "Please, Could you provide me more specific address?"
            }

        prompt = f"Find 1 Massage Envy location near {location}. Only get location's name and address."
        completion = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        print("Location: ", completion.choices[0].message.content)

        return completion.choices[0].message.content
    except Exception as err:
        print("Error: ", err)
        return {"nearest_location": "There are no nearest franchised."}

async def upsale_service(params):
    try:
        service = params.get('service').title()
        if not service:
            return {
                "upsale_service_infor": "Please, Could you provide me more specific address?"
            }
        print("\n".join(UPSALE_SERVICE[service]))

        print("****** End Upsale Service ******* \n")

        return "\n".join(UPSALE_SERVICE[service])
    except Exception as err:
        print("Error: ", err)
        return "There are no information detail for this service."


async def agent_filler(websocket, params):
    """
    Handle agent filler messages while maintaining proper function call protocol.
    """
    result = await prepare_agent_filler_message(websocket, **params)
    return result


async def end_call(websocket, params):
    """
    End the conversation and close the connection.
    """
    farewell_type = params.get("farewell_type", "general")
    result = await prepare_farewell_message(websocket, farewell_type)
    return result


