# PySuiteCRM  
[![GitHub issues](https://img.shields.io/github/issues/RussellJuma/PySuiteCRM)](https://github.com/RussellJuma/PySuiteCRM/issues)
[![GitHub stars](https://img.shields.io/github/stars/RussellJuma/PySuiteCRM)](https://github.com/RussellJuma/PySuiteCRM/stargazers)
[![GitHub license](https://img.shields.io/github/license/RussellJuma/PySuiteCRM)](https://github.com/RussellJuma/PySuiteCRM/blob/master/LICENSE)

PySuiteCRM ultilizes the SuiteCRM V8 API via Oauth2

PySuiteCRM supports all versions of SuiteCRM `7.10+`

## Contents

- [Installation](#Installation)
    - [OAuth2 Setup](#OAuth2_Setup)
    - [SuiteCRM Setup](#SuiteCRM_Setup)
    - [PySuiteCRM Setup](#PySuiteCRM_Setup)
- [Usage](#Usage)
    - [Create](#Create)
    - [Update](#Update)
    - [Get](#Get) 
    - [Delete](#Delete)
    - [Create_Relationship](#Create_Relationship)
    - [Get_Relationship](#Get_Relationship)
    - [Delete_Relationship](#Delete_Relationship)
    - [Fields](#Fields)
- [Performance](#Performance)
- [Contributing](#Contributing)
- [Credits](#Credits)
- [License](#License)

## Installation
### OAuth2_Setup
[SuiteCRM Oauth2 Setup source](https://docs.suitecrm.com/developer/api/developer-setup-guide/json-api/#_generate_private_and_public_key_for_oauth2)

SuiteCRM Api uses OAuth2 protocol, which needs public and private keys.

First, open a terminal and go to 
```
{{suitecrm.root}}/Api/V8/OAuth2
```

Generate a private key:
```bash
openssl genrsa -out private.key 2048
```

Generate a public key:
```bash
openssl rsa -in private.key -pubout -out public.key
```
If you need more information about generating, [please visit this page](https://oauth2.thephpleague.com/installation/).

The permission of the key files must be 600 or 660, so change it.
```bash
sudo chmod 600 private.key public.key
```

Make sure that the config files are owned by PHP
```bash
sudo chown www-data:www-data p*.key
```

OAuth2’s Authorization Server needs to set an encryption key for security reasons. This key has been gererated during the SuiteCRM installation and stored in the config.php under "oauth2_encryption_key". If you would like to change its value you may generate a new one by running and then storing the output in the config.php.
```bash
echo base64_encode(random_bytes(32)).PHP_EOL;
```
If you need more information about this issue, [please visit this page](https://oauth2.thephpleague.com/v5-security-improvements/)

<br/>

### SuiteCRM_Setup
Login as Admin and navigate to Admin>OAuth2 Clients and Tokens>New Client Credentials Client and generate Client Credentials.

## PySuiteCRM_Setup
Run the following command inside the directory of SuiteCRMPy
```bash
pip install -r requirements.txt
```

## Usage
### Import
```python
from SuiteCRM import SuiteCRM

suitecrm = SuiteCRM(client_id='client_id',
                 client_secret='client_secret',
                 url='https://your_suite_crm_location/Api/V8')

```

### Create
```python
result = suitecrm.Contacts.create(title='Software Engineer', first_name='Russell', last_name='Juma')
```

### Update
```python
result = suitecrm.Contacts.update(id='11129071-da4c-18ef-3107-5ead3a71d6fe', account_id='555-555-5555')
```

### Get
```python
# Request a record by id, returns a single record.
result = suitecrm.Contacts.get(id='11129071-da4c-18ef-3107-5ead3a71d6fe')

# Filter records by first and last name, returns a list of records.
result = suitecrm.Contacts.get(first_name='Russell', last_name='Juma')

# Filter records by first name, sort on last name, and only return full name and mobile phone in the records.
result = suitecrm.Contacts.get(fields=['full_name', 'phone_mobile'], first_name= 'Sarah', sort='last_name')

# return all records in a given module, default will pull 100 records per Get request to API.
result = suitecrm.Contacts.get_all()

```
Limitations
Get cannot filter on custom fields due to [bug #7285](https://github.com/salesagility/SuiteCRM/issues/7285) in SuiteCRM.

### Delete
```python
# Delete record by id
result = suitecrm.Contacts.delete(id='11129071-da4c-18ef-3107-5ead3a71d6fe')
```

### Create_Relationship
```python
# Create relationship between '11129071-da4c-18ef-3107-5ead3a71d6fe' in the Contacts and Accounts with id ='555-555-5555'
result = suitecrm.Contacts.create_relationship('11129071-da4c-18ef-3107-5ead3a71d6fe', 'Accounts', '555-555-5555')
```
### Get_Relationship
```python
# Get relationships between '11129071-da4c-18ef-3107-5ead3a71d6fe' in the Contacts with any in Accounts.
result = suitecrm.Contacts.get_relationship('11129071-da4c-18ef-3107-5ead3a71d6fe', 'Accounts')
```
### Delete_Relationship
```python
# Delete relationship between '11129071-da4c-18ef-3107-5ead3a71d6fe' in the Contacts and Accounts with id ='555-555-5555'
result = suitecrm.Contacts.delete('11129071-da4c-18ef-3107-5ead3a71d6fe', 'Accounts', '555-555-5555')
```

### Fields
```python
# Returns all the attributes in a module that can be set.
result = suitecrm.Contacts.fields()

['name', 'date_entered', 'date_modified', 'etc...']
```

## Performance
With Cache set to `True`, all Get, Create, Update requests are stored local within the module's cache. Cache is only 
pulled went the specific id is given,ie. `get(suitecrm.Contacts.id='11129071-da4c-18ef-3107-5ead3a71d6fe')` 

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Credits
- [Russell Juma](https://github.com/RussellJuma)

## License
PySuiteCRM is open source software licensed under the MIT license. See [LICENSE](LICENSE) for more information.