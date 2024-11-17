import gc, os
import logging
import json
import traceback

#create logger
logger = logging.getLogger()
l_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
l_handler.setFormatter(formatter)
logger.addHandler(l_handler)
logger.setLevel(logging.INFO)

co2_emission_per_mwh = 0.3  # Given 0.3 tons of CO2 per MWh

def delete_dataframe(df):
    del df
    gc.collect()


def calculate_cost(powerplants, fuels):
    """Calculate the cost per MWh for each plant considering fuel, efficiency, and CO2 cost."""
    # Calculate the cost per MWh for each powerplant
    for plant in powerplants:
        if plant["type"] == "gasfired":
            plant["cost_per_mwh"] = fuels["gas(euro/MWh)"] / plant["efficiency"] + co2_emission_per_mwh*fuels["co2(euro/ton)"]
        elif plant["type"] == "turbojet":
            plant["cost_per_mwh"] = fuels["kerosine(euro/MWh)"] / plant["efficiency"] + co2_emission_per_mwh*fuels["co2(euro/ton)"]
        elif plant["type"] == "windturbine":
            plant["cost_per_mwh"] = 0
            plant["pmax"] *= fuels["wind(%)"] / 100  # Adjust pmax based on wind availability

    return powerplants


def allocate_power(load, fuels, powerplants):
    """Allocate power generation to powerplants to match the total load while minimizing cost."""
    final_distribution = []
    # Step 1: Cost distribution
    powerplants = calculate_cost(powerplants, fuels)
    
    powerplants.sort(key=lambda p: p["cost_per_mwh"])
    # Step 2: Wind power calculation based on wind percentage
    wind_plants = [plant for plant in powerplants if plant['type'] == 'windturbine']
    
    # Allocate wind power first based on the wind percentage
    total_wind_power = 0
    for plant in wind_plants:
        total_wind_power += round(plant['pmax'], 1)
    remaining_load = load - total_wind_power
    
    if remaining_load <= 0:
        print("The wind power exceeds the load. JACKPOT")
        wind_load = load
        for plant in powerplants:
            if plant in wind_plants:
                if plant['pmax']>wind_load:
                    final_distribution.append({"name": plant["name"], "p": plant['pmax']})
                    wind_load -= plant['pmax']
                else: 
                    final_distribution.append({"name": plant["name"], "p": plant['pmax']})
    else:
        print(f"remaining load after wind: {remaining_load}")
        allocated_plants = []
        for plant in powerplants:
            print(f"remaining load: {remaining_load}")
            if plant in wind_plants:
                final_distribution.append({"name": plant["name"], "p": round(plant['pmax'], 1)})
                allocated_plants.append(plant["name"])
                continue
            elif remaining_load <= 0 and plant['name'] not in allocated_plants:
                # No more load to allocate
                final_distribution.append({"name": plant["name"], "p": 0.0})
                continue
            elif remaining_load <= 0 and plant['name'] in allocated_plants:
                # No more load to allocate
                continue

            # Distribute load evenly among identical plants with the same cost
            same_cost_plants = [p for p in powerplants if p["cost_per_mwh"] == plant["cost_per_mwh"] and p not in final_distribution]
            if len(same_cost_plants) > 1 and plant['pmin']*len(same_cost_plants)<remaining_load:
                # Evenly distribute load among these plants
                max_possible = sum(min(remaining_load, p["pmax"]) for p in same_cost_plants)
                if max_possible >= remaining_load:
                    share = remaining_load / len(same_cost_plants)
                    for p in same_cost_plants:
                        allocated = round(max(p["pmin"], min(p["pmax"], share)), 1)
                        final_distribution.append({"name": p["name"], "p": allocated})
                        allocated_plants.append(p["name"])
                        remaining_load -= allocated
                    continue
            else:
                # Allocate to this plant
                pmin, pmax = plant["pmin"], plant["pmax"]
                power = min(max(pmin, remaining_load), pmax)
                final_distribution.append({"name": plant["name"], "p": round(power, 1)})
                remaining_load -= power

        # Check if the load is fully allocated
        if remaining_load > 0:
            
            print("It is not possible to meet the load with the given powerplants.")
    
    return final_distribution


def productionplan_handler(event, context):
  try:
    method = event['httpMethod']
  
    if method == 'POST':  
        body = json.loads(event.get("body", "{}"))
        load = body.get("load")
        fuels = body.get("fuels")
        powerplants = body.get("powerplants")

        if load is None or fuels is None or powerplants is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters, 'powerplants' and 'load' and 'fuels' are required."}),
            }
        else:
            result = allocate_power(load, fuels, powerplants)
            print(json.dumps(result, indent=2))
        return {"body":{}}
    
    else:
      return {
          'statusCode': 404,
          'headers': {},
          'body': 'We only accept POST, not ' + method
      }
  except Exception as e:
    print(traceback.format_exc())
    body = json.dumps(str(e))
    return {
        'statusCode': 400,
        'headers': {},
        'body': body
    }


if __name__ == "__main__":
    """
    To be executed as script but also as a lambda
    """ 
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(BASE_PATH, 'tests/example_payloads')
    with open(f"{path}/payload2.json") as f:
        d = json.load(f)
    
    
    event={
    "resource": "/productionplan",
    "path": "/productionplan",
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json"
    },
    "body": json.dumps(d),
    "isBase64Encoded": False
    }
    
        
    productionplan_handler(event, {})


