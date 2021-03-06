import pymongo
from pymongo import MongoClient

def connect_database(connection_string, database_name):
    return MongoClient(host=connection_string)[database_name]


def get_all_countries(db):
    return [c for c in db.countries_summary.distinct('country')]


def get_all_documents(db, condition = None, global_agg = False, collection = 'countries_summary'):
    assert condition is not None or global_agg is True
    if condition is not None:
        return [doc for doc in db[collection].find(condition)]
    cur = db['global'].aggregate([
        {
            "$group": {
                "_id": "$date", 
                "confirmed": {"$sum": "$confirmed"},
                "deaths": {"$sum": "$deaths"},
                "recovered": {"$sum": "$recovered"}
            }      
        },
        {
            "$sort": {"_id": 1}
        }
    ])
    return [doc for doc in cur]


def get_daily_data(all_documents):
    return [(doc['date'].date(), max(doc['confirmed_daily'], 0), max(doc['deaths_daily'], 0), max(doc['recovered_daily'], 0)) for doc in all_documents]
def get_acc_data(all_documents, key):
    return [(doc[key].date(), doc['confirmed'], doc['deaths'], doc['recovered']) for doc in all_documents]
def get_k_latest_dates(db, k = 1):
    dates = db['global'].find({}, {"date": 1, "_id": 0}).distinct('date')
    return sorted(dates, reverse = True)[:k]
def get_coordinates_data(all_documents):
    result = []
    for doc in all_documents:
        if 'confirmed_daily' in doc and 'loc' in doc:
            result.append((doc['confirmed_daily'], doc['loc']['coordinates']))
    return result


