import json, base64
import requests

###############################################################################

creds = json.load(open('credentials.json','r'))

# Jira

jira_url     = creds['jira']['url']
jira_user    = creds['jira']['user']
jira_token   = creds['jira']['token']
jira_token64 = base64.b64encode(f'{jira_user}:{jira_token}'.encode()).decode()
jira_headers = {
    'Authorization': f'Basic {jira_token64}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Tempo

tempo_url     = creds['tempo']['url']
tempo_token   = creds['tempo']['token']
tempo_headers = {
    'Authorization': f'Bearer {tempo_token}'
}

###############################################################################

def get_issues(delta):

    issues   = []
    keys     = []
    start_at = 0
    while True:

        print(f'start at {start_at}')

        resp = requests.get(
            url=jira_url+'search',
            headers=jira_headers,
            params={
                'jql': f'updated >= \'{delta}\'',
                'maxResults': 100,
                'startAt': start_at
            }
        )

        issues += resp.json()['issues']
        for issue in issues:
            keys += issue['key']

        start_at += resp.json()['maxResults']
        if start_at >= resp.json()['total']:
            print('issues = '+str(resp.json()['total']))
            break

    return issues, keys

###############################################################################
def add_issue_tempo(issue):

    key = issue['key']
    print(f'add tempo {key}')

    total = 0
    types = {}
    url = f'{tempo_url}worklogs/issue/{key}'
    while url != '':

        resp = requests.get(
            url=url,
            headers=tempo_headers,
            params={
                'limit': 100
            }
        )

        for log in resp.json()['results']:
            log_type = [
                value['value'] \
                    for value in log['attributes']['values'] \
                        if value['key'] == '_Type_'
            ][0]
            log_type = f'Timespent Sum Tempo {log_type}'
            # convert seconds to hours
            hours = float(log['timeSpentSeconds'])/60/60
            types[log_type] = hours if log_type not in types else types[log_type] + hours
            total += hours

        url = resp.json()['metadata']['next'] if 'next' in resp.json()['metadata'] else ''
    
    issue['tempo'] = {
        'total': total,
        'types': types
    }
    return issue

###############################################################################

def main():

    # get issues from jira api updated from
    issues = get_issues('2021-03-17 00:00')

    # add tempo values
    tmp = []
    for issue in issues:
        tmp += [add_issue_tempo(issue)]
    issues = tmp
    del tmp

    print(json.dumps(issues,indent=2))

###############################################################################

if __name__ == '__main__':
    
    main()

###############################################################################