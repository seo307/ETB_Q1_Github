"""Task-8 claim witnesses over source-projected states; no tau2 imports, no external-root claims."""
from __future__ import annotations
import copy,hashlib,json,re
from pathlib import Path

PIN='c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4'
TASK='8'
SCHEMA='ETB_Q1E_TASK8_PROJECTION_v094'
CLAIMS=('C1_RESERVATION','C2_BOOKING_FIELDS','C3_COMMIT_CONSISTENCY','C4_PROCESS_AUTH_ROOT')
CERT='SUPPORTED_SOURCE_SCOPED'
REJECT='CONTRADICTED'
UNKNOWN='INDETERMINATE'
UNIDENTIFIED='NOT_IDENTIFIED'
USER='sophia_silva_7557'
FLIGHT='HAT271'
DATE='2024-05-26'
CERTIFICATE='certificate_8045380'
AMOUNT=348


def canonical(obj):return (json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(Path(p).read_bytes())
def passenger_digest(first,last,dob):
    # Public benchmark synthetic identity only, NOT an anonymization scheme for real PII.
    return sha(canonical([first,last,dob]))

TARGET_PASSENGERS=sorted([
    passenger_digest('Sophia','Silva','1957-10-05'),
    passenger_digest('Kevin','Smith','2001-04-12'),
])

class Missing(Exception): pass
class Invalid(Exception): pass

def need(obj,*path):
    current=obj
    for key in path:
        if not isinstance(current,dict) or key not in current:raise Missing('.'.join(map(str,path)))
        current=current[key]
    return current

def trial_checks(a,b):
    for obj,phase in ((a,'pre'),(b,'post')):
        if not isinstance(obj,dict):raise Invalid('SNAPSHOT_NOT_OBJECT')
        for field,expect in (('schema',SCHEMA),('source_pin',PIN),('task_id',TASK),('phase',phase)):
            if need(obj,field)!=expect:raise Invalid('SNAPSHOT_'+field.upper()+'_MISMATCH')
        if need(obj,'capture_origin') not in ('AUTHOR_CONSTRUCTED','PINNED_NATIVE_RUNTIME'):
            raise Invalid('INVALID_CAPTURE_ORIGIN')
    for field in ('nonce','run_binding','capture_origin'):
        if need(a,field)!=need(b,field):raise Invalid('PAIR_'+field.upper()+'_MISMATCH')
    if need(a,'observation_index')!=0 or need(b,'observation_index')!=1:
        raise Invalid('INVALID_OBSERVATION_INDEX')
    if a['capture_origin']=='AUTHOR_CONSTRUCTED' and b['capture_origin']!='AUTHOR_CONSTRUCTED':
        raise Invalid('MIXED_ROOT')


def _c1(a,b):
    pre_ids=need(a,'state','reservation_ids')
    post_ids=need(b,'state','reservation_ids')
    if not all(isinstance(x,list) and all(isinstance(i,str) for i in x)
               and len(x)==len(set(x)) for x in (pre_ids,post_ids)):
        raise Invalid('RESERVATION_ID_SET_INVALID')
    added=set(post_ids)-set(pre_ids)
    removed=set(pre_ids)-set(post_ids)
    created=next(iter(added)) if len(added)==1 else None
    record=need(b,'state','new_reservation')
    return {
      'one_new_reservation':len(added)==1,
      'none_removed':not removed,
      'reservation_id_bound':isinstance(record,dict) and need(record,'reservation_id')==created,
      'user_matches':isinstance(record,dict) and need(record,'user_id')==USER,
      'user_link_new':created is not None and created in need(b,'state','user_reservation_ids')
              and created not in need(a,'state','user_reservation_ids'),
      'user_links_preserved':set(need(a,'state','user_reservation_ids')).issubset(set(need(b,'state','user_reservation_ids'))),
    }

def _c2(a,b):
    record=need(b,'state','new_reservation')
    if record is None:return {'no_booking_record':False}
    if not isinstance(record,dict):raise Invalid('RECORD_TYPE_INVALID')
    segments=need(record,'flights')
    return {
      'origin_destination':need(record,'origin')=='ORD' and need(record,'destination')=='PHL',
      'flight_type':need(record,'flight_type')=='one_way',
      'cabin':need(record,'cabin')=='economy',
      'flight_date':isinstance(segments,list) and len(segments)==1 and isinstance(segments[0],dict)
            and segments[0].get('flight_number')==FLIGHT and segments[0].get('date')==DATE,
      'passenger_count':need(record,'passenger_count')==2,
      'passenger_identity_digests':sorted(need(record,'passenger_digests'))==TARGET_PASSENGERS,
      'payment_exact':need(record,'payment_history')==[{'payment_id':CERTIFICATE,'amount':AMOUNT}],
      'baggage_zero':need(record,'total_baggages')==0 and need(record,'nonfree_baggages')==0,
      'insurance_no':need(record,'insurance')=='no',
    }

def _c3(a,b):
    record=need(b,'state','new_reservation')
    if record is None:return {'no_booking_record':False}
    if not isinstance(record,dict):raise Invalid('RECORD_TYPE_INVALID')
    pre_f=need(a,'state','flight')
    post_f=need(b,'state','flight')
    pre_pay=need(a,'state','payment_methods')
    post_pay=need(b,'state','payment_methods')
    for obj in (pre_pay,post_pay):
        if not isinstance(obj,dict):raise Invalid('PAYMENT_MAP_INVALID')
    return {
      'seat_decrement':need(pre_f,'seats')-need(post_f,'seats')==2,
      'seat_nonnegative':need(post_f,'seats')>=0,
      'flight_price_matches':need(pre_f,'unit_price')==need(post_f,'unit_price')==174,
      'amount_matches_2x_price':need(record,'payment_history')==[{'payment_id':CERTIFICATE,'amount':2*need(pre_f,'unit_price')}],
      'certificate_before':CERTIFICATE in pre_pay and pre_pay[CERTIFICATE].get('source')=='certificate'
                  and pre_pay[CERTIFICATE].get('amount',-1)>=AMOUNT,
      'certificate_consumed':CERTIFICATE not in post_pay,
      'flight_key_consistent':need(pre_f,'flight_number')==need(post_f,'flight_number')==FLIGHT
                  and need(pre_f,'date')==need(post_f,'date')==DATE
                  and need(pre_f,'cabin')==need(post_f,'cabin')=='economy',
    }

def _run_claim(fn,a,b):
    try:
        predicates=fn(a,b)
        bad=sorted(k for k,ok in predicates.items() if ok is not True)
        return {'status':REJECT if bad else CERT,'reasons':bad,'obligations_checked':len(predicates)}
    except Missing as exc:
        return {'status':UNKNOWN,'reasons':['MISSING_FIELD:'+str(exc)]}
    except (Invalid,TypeError,ValueError,KeyError) as exc:
        return {'status':UNKNOWN,'reasons':['INVALID_FIELD:'+type(exc).__name__+':'+str(exc)[:160]]}

def verdict(pre,post):
    out={'schema':'ETB_Q1E_CLAIM_VERDICTS_v094','claims':{},'capture_origin':None,
         'independent_native_root':False,'policy_authorization_verified':False,
         'native_full_task_verified':False,'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False}
    try:
        trial_checks(pre,post)
        out['capture_origin']=pre['capture_origin']
    except (Missing,Invalid,TypeError,ValueError,KeyError) as exc:
        out['issues']=['INVALID_PAIR:'+str(exc)]
        for cl in CLAIMS:out['claims'][cl]={'status':UNKNOWN if cl!='C4_PROCESS_AUTH_ROOT' else UNIDENTIFIED,'reasons':['INVALID_PAIR']}
        return out
    for cl,fn in [('C1_RESERVATION',_c1),('C2_BOOKING_FIELDS',_c2),('C3_COMMIT_CONSISTENCY',_c3)]:
        out['claims'][cl]=_run_claim(fn,pre,post)
    for cl,parent in (('C2_BOOKING_FIELDS','C1_RESERVATION'),('C3_COMMIT_CONSISTENCY','C2_BOOKING_FIELDS')):
        parent_status=out['claims'][parent]['status']
        if parent_status!=CERT:
            desired=UNKNOWN if parent_status==UNKNOWN else REJECT
            out['claims'][cl]={'status':desired,'reasons':['PARENT_CLAIM_'+parent_status]}
    out['claims']['C4_PROCESS_AUTH_ROOT']={'status':UNIDENTIFIED,
        'reasons':['NO_INDEPENDENT_ADMIN_ROOT','NO_INDEPENDENT_NATIVE_EFFECT_SOURCE',
                   'NO_ENFORCEMENT_ORACLE','NO_COMMUNICATE_EVALUATION']}
    out['issues']=[]
    return out


def load_json_strict(p):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise ValueError('DUPLICATE_KEY:'+k)
            d[k]=v
        return d
    def bad(x):raise ValueError('NONFINITE:'+x)
    return json.loads(Path(p).read_bytes(),object_pairs_hook=unique,parse_constant=bad)


def verify_bundle(directory):
    p=Path(directory)
    errors=[]
    try:
        mf=load_json_strict(p/'MANIFEST.sha256.json')
        if not isinstance(mf,dict) or set(mf)!={'pre.json','post.json'}:
            raise Invalid('UNEXPECTED_FILE_SET')
        if {x.name for x in p.iterdir() if x.is_file()} != {'MANIFEST.sha256.json','pre.json','post.json'}:
            raise Invalid('DIR_EXTRA_FILE')
        for name,h in mf.items():
            if not re.fullmatch(r'[0-9a-f]{64}',h) or file_sha(p/name)!=h:
                raise Invalid('HASH_MISMATCH:'+name)
        pre=load_json_strict(p/'pre.json');post=load_json_strict(p/'post.json')
        result=verdict(pre,post)
        if result['issues']:errors.extend(result['issues'])
    except (OSError,ValueError,KeyError,TypeError,Invalid) as exc:
        errors.append(type(exc).__name__+':'+str(exc))
        result={'claims':{x:{'status':UNKNOWN} for x in CLAIMS},'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False}
    return {'status':'Q1E_WITNESS_BUNDLE_VERIFIED_SOURCE_SCOPED' if not errors else 'Q1E_WITNESS_BUNDLE_BLOCKED', 'issues':errors,'assessment':result}
