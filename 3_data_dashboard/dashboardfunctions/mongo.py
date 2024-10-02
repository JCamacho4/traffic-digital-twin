import datetime

import networkx as nx
from pymongo import MongoClient

from dashboardfunctions import constants


def get_database(database_name="TFG"):
    # Create a connection using MongoClient
    client = MongoClient(constants.MONGO_TOKEN)

    # Create the database if it doesn't exist, otherwise return the existing database
    return client[database_name]


def get_available_graphs_by_date(db, from_date, to_date):
    return db["dates"].find({"datetime": {"$gte": from_date, "$lte": to_date}}).sort("datetime", 1)


def get_graph_by_filename(db, filename):
    mongo_object = db["graphs"].find_one({"filename": filename})
    if mongo_object:
        return nx.node_link_graph(mongo_object)
    else:
        return None


def get_edges_by_filename(db, filename):
    mongo_object = db["graphs"].find_one({"filename": filename})
    if mongo_object:
        return mongo_object["links"]
    else:
        return None


def get_data_from_graphs_with_filters_by_name(db, from_date, to_date, names_pattern, highway_types, start_hour_minute,
                                              end_hour_minute):
    previous_to_group = __generate_aggregation_previos_to_group(from_date, to_date, names_pattern, highway_types,
                                                                start_hour_minute,
                                                                end_hour_minute)
    return db["graphs"].aggregate([
        previous_to_group[0],
        previous_to_group[1],
        previous_to_group[2],
        {
            "$group": {
                "_id": "$links.name",
                "minTrafficLevel": {"$min": "$links.traffic_level"},
                "maxTrafficLevel": {"$max": "$links.traffic_level"},
                "avgTrafficLevel": {"$avg": "$links.traffic_level"},
                "medianTrafficLevel": {
                    "$median": {
                        "input": "$links.traffic_level",
                        "method": "approximate"
                    }
                },

                "minCurrentSpeed": {"$min": "$links.current_speed"},
                "maxCurrentSpeed": {"$max": "$links.current_speed"},
                "avgCurrentSpeed": {"$avg": "$links.current_speed"},
                "medianCurrentSpeed": {
                    "$median": {
                        "input": "$links.current_speed",
                        "method": "approximate"
                    }
                },

                "amountOfData": {"$sum": 1},
                "amountOfTimesInterpolated": {"$sum": {"$cond": {"if": "$links.api_data", "then": 0, "else": 1}}}
            }
        },
    ])


def __generate_aggregation_previos_to_group(from_date, to_date, names_pattern, highway_types, start_hour_minute,
                                            end_hour_minute):
    start_hour_int = int(start_hour_minute.split(":")[0])
    start_minute_int = int(start_hour_minute.split(":")[1])

    end_hour_int = int(end_hour_minute.split(":")[0])
    end_minute_int = int(end_hour_minute.split(":")[1])

    print(start_hour_int, start_minute_int, end_hour_int, end_minute_int)

    match_conditions = {
        "datetime": {
            "$gte": from_date,
            "$lte": to_date
        },
        "hour_int": {
            "$gte": start_hour_int,
            "$lte": end_hour_int
        },
        "$expr": {
            "$and": [
                # Handle start hour minute filter
                {
                    "$cond": [
                        {"$eq": ["$hour_int", start_hour_int]},  # Only for the start hour
                        {"$gte": ["$minute_int", start_minute_int]},  # Remove the first X minutes
                        True  # Don't apply to other hours
                    ]
                },
                # Handle end hour minute filter
                {
                    "$cond": [
                        {"$eq": ["$hour_int", end_hour_int]},  # Only for the end hour
                        {"$lte": ["$minute_int", end_minute_int]},  # Remove the last Y minutes
                        True  # Don't apply to other hours
                    ]
                }
            ]
        }
    }

    # Add the name patterns condition if the list is not empty
    match_conditions_after_unwind = {
        "links.highway": {
            "$in": highway_types
        },
    }

    if len(names_pattern) > 0:
        regex_patterns = [{"links.name": {"$regex": pattern, "$options": "i"}} for pattern in names_pattern]
        match_conditions_after_unwind["$or"] = regex_patterns

    return {"$match": match_conditions}, {"$unwind": "$links"}, {"$match": match_conditions_after_unwind}


def get_data_from_graphs_with_filters_by_hours(db, from_date, to_date, names_pattern, highway_types, start_hour_minute,
                                               end_hour_minute):
    previous_to_group = __generate_aggregation_previos_to_group(from_date, to_date, names_pattern, highway_types,
                                                                start_hour_minute, end_hour_minute)

    return db["graphs"].aggregate([
        previous_to_group[0],
        previous_to_group[1],
        previous_to_group[2],

        {
            "$group": {
                # Aproximate the _id to the nearest 30min, so we can group by half an hour, taking into account the 'hour_int' and 'minute_int' fields
                "_id": {
                    "hour": "$hour_int",
                    "halfHour": {
                        "$cond": [
                            {"$lt": ["$minute_int", 30]},
                            "00",
                            "30"
                        ]
                    }
                },
                "minTrafficLevel": {"$min": "$links.traffic_level"},
                "maxTrafficLevel": {"$max": "$links.traffic_level"},
                "avgTrafficLevel": {"$avg": "$links.traffic_level"},
                "medianTrafficLevel": {
                    "$median": {
                        "input": "$links.traffic_level",
                        "method": "approximate"
                    }
                },

                "minCurrentSpeed": {"$min": "$links.current_speed"},
                "maxCurrentSpeed": {"$max": "$links.current_speed"},
                "avgCurrentSpeed": {"$avg": "$links.current_speed"},
                "medianCurrentSpeed": {
                    "$median": {
                        "input": "$links.current_speed",
                        "method": "approximate"
                    }
                },

                "amountOfData": {"$sum": 1},
                "amountOfTimesInterpolated": {"$sum": {"$cond": {"if": "$links.api_data", "then": 0, "else": 1}}}
            },
        },
        {
            "$project": {
                "timeSort": {
                    "$concat": [
                        {"$cond": [{"$lt": ["$_id.hour", 10]}, "0", ""]},
                        {"$toString": "$_id.hour"},
                        {"$cond": [{"$lt": ["$_id.halfHour", "30"]}, "0", ""]},
                        "$_id.halfHour"
                    ]
                },
                "_id": {
                    "$concat": [
                        {"$cond": [{"$lt": ["$_id.hour", 10]}, "0", ""]},
                        {"$toString": "$_id.hour"},
                        ":",
                        "$_id.halfHour",
                        "-",
                        {"$cond": [
                            {"$lt": [{"$add": ["$_id.hour", {"$cond": [{"$eq": ["$_id.halfHour", "30"]}, 1, 0]}]}, 10]},
                            "0",
                            ""
                        ]},
                        {"$toString": {
                            "$mod": [{"$add": ["$_id.hour", {"$cond": [{"$eq": ["$_id.halfHour", "30"]}, 1, 0]}]},
                                     24]}},
                        ":",
                        {"$cond": [{"$eq": ["$_id.halfHour", "00"]}, "30", "00"]}
                    ]
                },
                "minTrafficLevel": 1,
                "maxTrafficLevel": 1,
                "avgTrafficLevel": 1,
                "medianTrafficLevel": 1,
                "minCurrentSpeed": 1,
                "maxCurrentSpeed": 1,
                "avgCurrentSpeed": 1,
                "medianCurrentSpeed": 1,
                "amountOfData": 1,
                "amountOfTimesInterpolated": 1
            }
        },
        {
            "$sort": {
                "timeSort": 1
            }
        }
    ])


def get_data_from_graphs_with_filters_by_weekday(db, from_date, to_date, names_pattern, highway_types,
                                                 start_hour_minute,
                                                 end_hour_minute):
    previous_to_group = __generate_aggregation_previos_to_group(from_date, to_date, names_pattern, highway_types,
                                                                start_hour_minute, end_hour_minute)

    return db["graphs"].aggregate([
        previous_to_group[0],
        previous_to_group[1],
        previous_to_group[2],
        {
            "$group": {
                "_id": "$day_of_week",
                "minTrafficLevel": {"$min": "$links.traffic_level"},
                "maxTrafficLevel": {"$max": "$links.traffic_level"},
                "avgTrafficLevel": {"$avg": "$links.traffic_level"},
                "medianTrafficLevel": {
                    "$median": {
                        "input": "$links.traffic_level",
                        "method": "approximate"
                    }
                },

                "minCurrentSpeed": {"$min": "$links.current_speed"},
                "maxCurrentSpeed": {"$max": "$links.current_speed"},
                "avgCurrentSpeed": {"$avg": "$links.current_speed"},
                "medianCurrentSpeed": {
                    "$median": {
                        "input": "$links.current_speed",
                        "method": "approximate"
                    }
                },

                "amountOfData": {"$sum": 1},
            },
        }
    ])


if __name__ == "__main__":
    database = get_database("TFG")

    import time

    # mongo_cursor = get_data_from_graphs_with_filters_by_name(database, datetime.datetime(2024, 5, 8, 0, 0, 0),
    #                                                          datetime.datetime(2024, 5, 10, 23, 59, 59),
    #                                                          [],
    #                                                          ['secondary', 'motorway', 'motorway_link', 'primary',
    #                                                           'tertiary', 'residential',
    #                                                           'primary_link', 'tertiary_link', 'secondary_link',
    #                                                           'living_street'], "00:00", "23:00")
    #
    # print(list(mongo_cursor))
    start = time.time()
    mongo_cursor = get_data_from_graphs_with_filters_by_hours(database, datetime.datetime(2024, 5, 8, 0, 0, 0),
                                                              datetime.datetime(2024, 5, 9, 23, 59, 59),
                                                              [],
                                                              ['secondary', 'motorway', 'motorway_link', 'primary',
                                                               'tertiary', 'residential',
                                                               'primary_link', 'tertiary_link', 'secondary_link',
                                                               'living_street'], "00:00", "23:00")
    end = time.time()
    print(list(mongo_cursor))

    print("\n\nTime to execute 5/8 00:00 to 5/9 23:59 (taking everything [min,max,avg,median]) ->  ", end - start)

    start = time.time()
    mongo_cursor = get_data_from_graphs_with_filters_by_hours(database, datetime.datetime(2024, 5, 8, 0, 0, 0),
                                                              datetime.datetime(2024, 5, 31, 23, 59, 59),
                                                              [],
                                                              ['secondary', 'motorway', 'motorway_link', 'primary',
                                                               'tertiary', 'residential',
                                                               'primary_link', 'tertiary_link', 'secondary_link',
                                                               'living_street'], "00:00", "23:00")
    end = time.time()
    print(list(mongo_cursor))
    print("\n\nTime to execute 5/8 00:00 to 5/31 23:59 (taking everything [min,max,avg,median]) ->  ", end - start)
