import json
import uuid
import atexit
import math
import datetime
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError, InvalidClientError
from oauthlib.oauth2.rfc6749.errors import CustomOAuth2Error


class SuiteCRM:

    def __init__(self, client_id, client_secret, url, cache=False, cache_timeout=300):

        self.client_id = client_id
        self.client_secret = client_secret
        self.baseurl = url
        self.cache = cache
        self.cache_timeout_seconds = cache_timeout
        self.logout_on_exit = False
        self.headers = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                       'Chrome/85.0.4183.83 Safari/537.36'
        self._login()
        self._modules()

    def _modules(self):
        self.Accounts = Module(self, 'Accounts')
        self.Bugs = Module(self, 'Bugs')
        self.Calendar = Module(self, 'Calendar')
        self.Calls = Module(self, 'Calls')
        self.Cases = Module(self, 'Cases')
        self.Campaigns = Module(self, 'Campaigns')
        self.Contacts = Module(self, 'Contacts')
        self.Documents = Module(self, 'Documents')
        self.Email = Module(self, 'Email')
        self.Emails = Module(self, 'Emails')
        self.Employees = Module(self, 'Employees')
        self.Leads = Module(self, 'Leads')
        self.Lists = Module(self, 'Lists')
        self.Meetings = Module(self, 'Meetings')
        self.Notes = Module(self, 'Notes')
        self.Opportunities = Module(self, 'Opportunities')
        self.Projects = Module(self, 'Projects')
        self.Spots = Module(self, 'Spots')
        self.Surveys = Module(self, 'Surveys')
        self.Target = Module(self, 'Target')
        self.Targets = Module(self, 'Targets')
        self.Tasks = Module(self, 'Tasks')
        self.Templates = Module(self, 'Templates')

    def _refresh_token(self):
        """
        Fetch a new token from from token access url, specified in config file.
        :return: None
        """
        try:
            self.OAuth2Session.fetch_token(token_url=self.baseurl[:-2] + 'access_token',
                                           client_id=self.client_id,
                                           client_secret=self.client_secret)
        except InvalidClientError:
            exit('401 (Unauthorized) - client id/secret')
        except CustomOAuth2Error:
            exit('401 (Unauthorized) - client id')
        # Update configuration file with new token'
        with open('AccessToken.txt', 'w+') as file:
            file.write(str(self.OAuth2Session.token))

    def _login(self):
        """
        Checks to see if a Oauth2 Session exists, if not builds a session and retrieves the token from the config file,
        if no token in config file, fetch a new one.

        :return: None
        """
        # Does session exist?
        if not hasattr(self, 'OAuth2Session'):
            client = BackendApplicationClient(client_id=self.client_id)
            self.OAuth2Session = OAuth2Session(client=client,
                                               client_id=self.client_id)
            self.OAuth2Session.headers.update({"User-Agent": self.headers,
                                               'Content-Type': 'application/json'})
            with open('AccessToken.txt', 'w+') as file:
                token = file.read()
                if token == '':
                    self._refresh_token()
                else:
                    self.OAuth2Session.token = token
        else:
            self._refresh_token()

        # Logout on exit
        if self.logout_on_exit:
            atexit.register(self._logout)

    def _logout(self):
        """
        Logs out current Oauth2 Session
        :return: None
        """
        url = '/logout'
        self.request(f'{self.baseurl}{url}', 'post')
        with open('AccessToken.txt', 'w+') as file:
            file.write('')

    def request(self, url, method, parameters=''):
        """
        Makes a request to the given url with a specific method and data. If the request fails because the token expired
        the session will re-authenticate and attempt the request again with a new token.

        :param url: (string) The url
        :param method: (string) Get, Post, Patch, Delete
        :param parameters: (dictionary) Data to be posted

        :return: (dictionary) Data
        """
        data = json.dumps({"data": parameters})
        try:
            the_method = getattr(self.OAuth2Session, method)
        except AttributeError:
            return

        try:
            if parameters == '':
                data = the_method(url)
            else:
                data = the_method(url, data=data)
        except TokenExpiredError:
            self._refresh_token()
            if parameters == '':
                data = the_method(url)
            else:
                data = the_method(url, data=data)

        # Revoked Token
        attempts = 0
        while data.status_code == 401 and attempts < 1:
            self._refresh_token()
            if parameters == '':
                data = the_method(url)
            else:
                data = the_method(url, data=data)
            attempts += 1
        if data.status_code == 401:
            exit('401 (Unauthorized) client id/secret has been revoked, new token was attempted and failed.')

        # Database Failure
        # SuiteCRM does not allow to query by a custom field see README, #Limitations
        if data.status_code == 400 and 'Database failure.' in data.content.decode():
            raise Exception(data.content.decode())

        return json.loads(data.content)


class Module:

    def __init__(self, suitecrm, module_name):
        self.module_name = module_name
        self.suitecrm = suitecrm
        self.cache = {}
        self.cache_time = {}
        self.cache_status = self.suitecrm.cache
        self.cache_timeout_seconds = self.suitecrm.cache_timeout_seconds

    def _cache_delete(self, **by):
        """
        Clears cache by define by an option
        :param by: (string) Option of all,id, or old cache
        :return: None
        """
        if 'all' in by and by['all']:
            self.cache.clear()
        elif 'id' in by and by['id'] in self.cache and self.cache_status:
            del self.cache[by['id']]
            del self.cache_time[by['id']]
        elif 'old' in by and by['old']:
            for record, time in self.cache.items():
                if time + datetime.timedelta(seconds=self.cache_timeout_seconds) <= datetime.datetime.now():
                    del self.cache[record]
                    del self.cache_time[record]

    def _cache_set(self, request):
        """
        Set cache with the id of each record as the key
        :param request: (JSON) data
        :return: (dictionary) of request, or (JSON) of request if it fails
        """
        try:
            if len(request['data']) != 0:
                # A single record
                if type(request['data']) is dict:
                    if self.cache_status:
                        self.cache[request['data']['id']] = request['data']
                        self.cache_time[request['data']['id']] = datetime.datetime.now()
                    return request['data']
                # A list of records
                if self.cache_status:
                    for record in request['data']:
                        self.cache[record['id']] = record
                        self.cache_time[record['id']] = datetime.datetime.now()
                return request['data']
        except:
            pass
        return request

    def _cache_get(self, id):
        """
        Retrieves from the cache the record, if cache is expire it will renew
        :param id: (string) id of the record
        :return: (dictionary) record
        """
        if id in self.cache and self.cache_status:
            # Expired
            if self.cache_time[id] + datetime.timedelta(seconds=self.cache_timeout_seconds) >= datetime.datetime.now():
                return self.cache[id]
            else:
                # Expire record, delete cache and request new
                self._cache_delete(id=id)
                return self.get(id=id)

    def create(self, **attributes):
        """
        Creates a record with given attributes
        :param attributes: (**kwargs) fields with data you want to populate the record with.

        :return: (dictionary) The record that was created with the attributes.
        """
        url = '/module'
        data = {'type': self.module_name, 'id': str(uuid.uuid4()), 'attributes': attributes}
        return self._cache_set(self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'post', data))

    def delete(self, id):
        """
        Delete a specific record by id.
        :param id: (string) The record id within the module you want to delete.

        :return: (dictionary) Confirmation of deletion of record.
        """
        # Delete
        url = f'/module/{self.module_name}/{id}'
        self._cache_delete(id=id)
        return self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'delete')

    def fields(self):
        """
        Gets all the attributes that can be set in a record.
        :return: (list) All the names of attributes in a record.
        """
        # Get total record count
        url = f'/module/{self.module_name}?page[number]=1&page[size]=1'
        return list(self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'get')['data'][0]['attributes'].keys())

    def get(self, fields=None, sort=None, **filters):
        """
        Gets records given a specific id or filters, can be sorted only once, and the fields returned for each record
        can be specified.

        :param fields: (list) A list of fields you want to be returned from each record.
        :param sort: (string) The field you want the records to be sorted by.
        :param filters: (**kwargs) fields that the record has that you want to filter on.

        Important notice: we don’t support multiple level sorting right now!

        :return: (dictionary/list) A list or dictionary of record(s) that meet the filter criteria.
                 (list) If more than one record
                 (dictionary) if a single record
        """
        # Fields Constructor
        if fields:
            fields = f'?fields[{self.module_name}]=' + ', '.join([fields])
            url = f'/module/{self.module_name}{fields}&filter'
        else:
            url = f'/module/{self.module_name}?filter'

        # Filter Constructor
        for field, value in filters.items():
            url = f'{url}[{field}][eq]={value}and&'
        url = url[:-4]

        # Sort
        if sort:
            url = f'{url}&sort=-{sort}'

        # Execute
        if 'id' in filters and len(filters) == 1 and filters['id'] in self.cache:
            return self._cache_get(id=filters['id'])
        else:
            return self._cache_set(self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'get'))

    def get_all(self, record_per_page=100):
        """
        Gets all the records in the module.
        :return: (list) All the records(dictionary) within a module.
        """
        # Get total record count
        url = f'/module/{self.module_name}?page[number]=1&page[size]=1'
        pages = math.ceil(self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'get')['meta']['total-pages'] /
                          record_per_page) + 1
        result = []
        for page in range(1, pages):
            url = f'/module/{self.module_name}?page[number]={page}&page[size]={record_per_page}'
            result.extend(self._cache_set(self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'get')))
        return result

    def update(self, id, **attributes):
        """
        updates a record.

        :param id: (string) id of the current module record.
        :param attributes: (**kwargs) fields inside of the record to be updated.

        :return: (dictionary) The updated record
        """
        url = '/module'
        data = {'type': self.module_name, 'id': id, 'attributes': attributes}
        return self._cache_set(self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'patch', data))

    def get_relationship(self, id, related_module_name):
        """
        returns the relationship between this record and another module.

        :param id: (string) id of the current module record.
        :param related_module_name: (string) the module name you want to search relationships for, ie. Contacts.

        :return: (dictionary) A list of relationships that this module's record contains with the related module.
        """
        url = f'/module/{self.module_name}/{id}/relationships/{related_module_name.lower()}'
        return self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'get')

    def create_relationship(self, id, related_module_name, related_bean_id):
        """
        Creates a relationship between 2 records.

        :param id: (string) id of the current module record.
        :param related_module_name: (string) the module name of the record you want to create a relationship,
               ie. Contacts.
        :param related_bean_id: (string) id of the record inside of the other module.

        :return: (dictionary) A record that the relationship was created.
        """
        # Post
        url = f'/module/{self.module_name}/{id}/relationships'
        data = {'type': related_module_name.capitalize(), 'id': related_bean_id}
        return self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'post', data)

    def delete_relationship(self, id, related_module_name, related_bean_id):
        """
        Deletes a relationship between 2 records.

        :param id: (string) id of the current module record.
        :param related_module_name: (string) the module name of the record you want to delete a relationship,
               ie. Contacts.
        :param related_bean_id: (string) id of the record inside of the other module.

        :return: (dictionary) A record that the relationship was deleted.
        """
        url = f'/module/{self.module_name}/{id}/relationships/{related_module_name.lower()}/{related_bean_id}'
        return self.suitecrm.request(f'{self.suitecrm.baseurl}{url}', 'delete')
