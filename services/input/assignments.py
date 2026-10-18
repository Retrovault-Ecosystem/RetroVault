"""Never infer persistent identity from a display name or enumeration index."""

def resolve_players(profile, devices):
    if profile['mode']=='existing':
        return ()
    result=[];used=set()
    for player in profile['players']:
        if player['kind']=='keyboard':
            result.append((player,None));continue
        saved=player['device']
        matches=[d for d in devices if d['guid']==saved['guid'] and
                 ((saved['serial'] and d['serial']==saved['serial']) or
                  (not saved['serial'] and d['session']==saved['session'] and d['instance']==saved['instance']))]
        if len(matches)!=1:
            raise ValueError('Assigned controller is disconnected or ambiguous; select it again in Settings.')
        device=matches[0]
        if device['instance'] in used:
            raise ValueError('The same controller cannot be assigned to both players.')
        used.add(device['instance']);result.append((player,device))
    return tuple(result)
