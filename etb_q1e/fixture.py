"""Authored contrast fixture; never described as a native or external observation."""
from __future__ import annotations
import copy
from .core import SCHEMA,PIN,TASK,USER,CERTIFICATE,TARGET_PASSENGERS

def fixture():
    common={'schema':SCHEMA,'source_pin':PIN,'task_id':TASK,'nonce':'DEVELOPMENT_SYNTHETIC_TASK8','run_binding':'AUTHOR_FIXTURE','capture_origin':'AUTHOR_CONSTRUCTED'}
    pre={**common,'phase':'pre','observation_index':0,'state':{
        'reservation_ids':['WUNA5K','PREV000'], 'user_reservation_ids':['WUNA5K'],
        'new_reservation':None,
        'flight':{'flight_number':'HAT271','date':'2024-05-26','cabin':'economy','seats':8,'unit_price':174},
        'payment_methods':{CERTIFICATE:{'source':'certificate','amount':500}},
    }}
    post=copy.deepcopy(pre)
    post['phase']='post';post['observation_index']=1
    post['state']['reservation_ids'].append('ETBNEW')
    post['state']['user_reservation_ids'].append('ETBNEW')
    post['state']['flight']['seats']=6
    del post['state']['payment_methods'][CERTIFICATE]
    post['state']['new_reservation']={
     'reservation_id':'ETBNEW','user_id':USER,'origin':'ORD','destination':'PHL',
     'flight_type':'one_way','cabin':'economy','flights':[{'flight_number':'HAT271','date':'2024-05-26'}],
     'passenger_count':2,'passenger_digests':TARGET_PASSENGERS,'payment_history':[{'payment_id':CERTIFICATE,'amount':348}],
     'total_baggages':0,'nonfree_baggages':0,'insurance':'no',
    }
    return pre,post

# One-field mutations. Each negative is paired with the positive before witness projection.
MUTATIONS={
    'missing_new_id':('C1_RESERVATION',('state','reservation_ids'),['WUNA5K','PREV000']),
    'wrong_record_user':('C1_RESERVATION',('state','new_reservation','user_id'),'other_user'),
    'missing_user_link':('C1_RESERVATION',('state','user_reservation_ids'),['WUNA5K']),
    'remove_old_reservation':('C1_RESERVATION',('state','reservation_ids'),['WUNA5K','ETBNEW']),
    'wrong_origin':('C2_BOOKING_FIELDS',('state','new_reservation','origin'),'SFO'),
    'wrong_flight_type':('C2_BOOKING_FIELDS',('state','new_reservation','flight_type'),'round_trip'),
    'wrong_cabin':('C2_BOOKING_FIELDS',('state','new_reservation','cabin'),'business'),
    'wrong_flight_date':('C2_BOOKING_FIELDS',('state','new_reservation','flights'),[{'flight_number':'HAT271','date':'2024-05-27'}]),
    'wrong_passenger_count':('C2_BOOKING_FIELDS',('state','new_reservation','passenger_count'),1),
    'wrong_passenger_identity':('C2_BOOKING_FIELDS',('state','new_reservation','passenger_digests'),['impostor','impostor2']),
    'wrong_payment':('C2_BOOKING_FIELDS',('state','new_reservation','payment_history'),[{'payment_id':'credit_card_1','amount':348}]),
    'wrong_baggage':('C2_BOOKING_FIELDS',('state','new_reservation','total_baggages'),1),
    'wrong_insurance':('C2_BOOKING_FIELDS',('state','new_reservation','insurance'),'yes'),
    'seat_not_decremented':('C3_COMMIT_CONSISTENCY',('state','flight','seats'),8),
    'flight_price_altered':('C3_COMMIT_CONSISTENCY',('state','flight','unit_price'),190),
    'certificate_unconsumed':('C3_COMMIT_CONSISTENCY',('state','payment_methods'),{CERTIFICATE:{'source':'certificate','amount':500}}),
}

def mutated(post,name):
    _,path,value=MUTATIONS[name]
    out=copy.deepcopy(post);obj=out
    for x in path[:-1]:obj=obj[x]
    obj[path[-1]]=copy.deepcopy(value)
    return out

def delete_at(obj,path):
    out=copy.deepcopy(obj);parent=out
    for x in path[:-1]:parent=parent[x]
    del parent[path[-1]]
    return out
