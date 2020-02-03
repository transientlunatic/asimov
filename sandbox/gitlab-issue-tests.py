from supervisor import gitlab, mattermost
from supervisor import config
from supervisor import condor

server = gitlab.gitlab.Gitlab('https://git.ligo.org', private_token=config.get("gitlab", "token"))
repository = server.projects.get(3816)

events = gitlab.find_events(repository)

mattermost = mattermost.Mattermost()

message = """# Run updates\n"""
message += """| Event | Cluster | Production | Status |\n"""
message += """|---|---|---|---|\n"""

for event in events:
    if "Prod0" in event.data:
        print(event.title)
        print(event.state)
        print(event.data['Prod0'])
        cluster = event.data['Prod0']
        try:
            job = condor.CondorJob(event.data['Prod0'])
            status = job.status

        except ValueError:
            status = "Not running"

        message += f"""| {event.title} | {cluster} | Prod0 | {status} |\n"""

    elif "Prod1" in event.data:
        print(event.title)
        print(event.state)
        print(event.data['Prod1'])
        cluster = event.data['Prod1']
        try:
            job = condor.CondorJob(event.data['Prod1'])
            status = job.status

        except ValueError:
            status = "Not running"

        message += f"""|               | {cluster} | Prod1 | {status} |\n"""        

mattermost.submit_payload(message)
