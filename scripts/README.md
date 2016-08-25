# Steps to run

### Configuration

##### Generate a token
You will need to generate a personal access token on the OSF to run this script. Visit:

- [https://staging.osf.io/settings/tokens/](https://staging.osf.io/settings/tokens/)  _or_
- [https://osf.io/settings/tokens/](https://osf.io/settings/tokens/)

to do this.

![example](https://raw.githubusercontent.com/CenterForOpenScience/lookit/develop/scripts/pat-example.png)

**Make sure to save this token's value! You will not be able to retrieve it again.**

##### Create a .env

Create a new file name .env in this directory. It should look like:

```
OSF_ACCESS_TOKEN=<your-staging-access-token>
JAM_URL=https://staging-metadata.osf.io
JAM_NAMESPACE=experimenter
```

or

```
OSF_ACCESS_TOKEN=<your-access-token>
JAM_URL=https://metadata.osf.io
JAM_NAMESPACE=lookit
```

Each the scripts accept an argument to point to a specific .env file (e.g. '.env-stage' or '.env-prod'). For example:

```bash
python client.py -c .env-stage
```

##### Install

1. Create a virtualenvironment using a python 2.7.X executable
2. `pip install -r requirements.txt`

### Included Code

#### client.py

This file mostly contains some examples and utilites for interacting with the JamDB API.

#### sengrid_client.py

This file gives some examples of using the sendgrid Python client to interact with SendGrid's suppression groups and send emails to users. 
You can add the`SENDGRID_KEY` setting to your .env to avoid having to pass an `apikey` argument to the sendgrid_client.SendGrid constructor.

#### email_migrated_users.py

This script fetches all of the users with a non-null value of `migratedFrom` attribute and issues a password reset request for them. Usage:
`python email_migrated_users.py -DR true|false -D true|false -V 0|1|2`

where:

	*`-DR` specifies whether this is a 'dry-run' or not. Setting this flag true (default) will make the script only log who password requests are sent to (not actually sending emails). Set this false to actaully send emails.
	
	*`-D` specifies whether or not to use debug mode. Debug mode means if an unexpected server response is seen an IPDB shell is opened to inspect the program state.
	
	*`-V` specifies verbositiy. Use integers 0-2 to pick a logging level (0=NOTSET, 1=INFO, 2=DEBUG)



