import requests
import cachecontrol
import json
from copy import deepcopy

# We are migrating from popit to popit_ng better have an abstraction layer
class BasePopoloProvider(object):
    base_url = None

    def __init__(self):
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)

    def fetch_entity(self, entity, entity_id, language):
        raise NotImplementedError()

    def fetch_entities(self, entity, language, page=0):
        raise NotImplementedError()

    def search_entities(self, entity, language, page=0, search_params={}):
        raise NotImplementedError()

    def create_entity(self, entity, language, api_key, form):
        raise NotImplementedError()

    def update_entity(self, entity, entity_id, data, language, form):
        raise NotImplementedError()


# TODO: Use cache control
class PopitNgProvider(BasePopoloProvider):
    base_url = "http://api.popit.sinarproject.org"

    # Maintain meta data
    def get_request(self, url, params={}, headers={}):
        r = self.session.get(url, headers=headers, params=params)
        status_code = r.status_code
        data = r.json()
        return status_code, data

    def fetch_entity(self, entity, entity_id, language):
        url = "%s/%s/%s/%s/" % (self.base_url, language, entity, entity_id)
        status_code, output = self.get_request(url)
        data = {}

        for key in output["result"]:
            if key in ("person", "organization", "parent", "post", "membership", "member"):
                if output["result"][key] and "label" in output["result"][key]:
                    data[key] = output["result"][key]["label"]
                if output["result"][key] and "name" in output["result"][key]:
                    data[key] = output["result"][key]["name"]
            else:
                data[key] = output["result"][key]
        return status_code, data

    # have a separate one because pagination meta data is needed
    def fetch_entities(self, entity, language, page=0):
        url = "%s/%s/%s/" % (self.base_url, language, entity)
        # 0 is False in python. 
        params = {}
        if page:
            params["page"] = page
        status_code, data = self.get_request(url, params)
        return status_code, data

    def search_entities(self, entity, language, page=0, search_params={}, fetch_from_id=True):
        url = "%s/%s/%s/%s/" % (self.base_url, language, "search", entity)
        param = {}
        search_strings = []
        for key, value in search_params.items():
            search_strings.append("%s:%s" % (key, value))
        
        search_key = " AND ".join(search_strings)
        param["q"] = search_key
        if page:
            param["page"] = page
        status_code, data = self.get_request(url, params=param)
        result = []
        for item in data["results"]:
            temp = item
            if fetch_from_id:
                if temp.get("parent_id"):
                    _, parent = self.fetch_entity("organizations", temp["parent_id"], language)
                    temp["parent"] = parent["name"]
                else:
                    temp["parent"] = None

                if temp.get("organization_id"):
                    _, organization = self.fetch_entity("organizations", temp["organization_id"], language)
                    temp["organization"] = organization
                else:
                    temp["organization"] = None

                if temp.get("person_id"):
                    _, person = self.fetch_entity("persons", temp["person_id"], language)
                    temp["person"] = person
                else:
                    temp["person"] = None

                if temp.get("post_id"):
                    _, post = self.fetch_entity("posts", temp["post_id"], language)
                    temp["post"] = post
                else:
                    temp["post"] = None
            result.append(temp)
        data["results"] = result

        return status_code, data

    def create_entity(self, entity, language, api_key, form):
        url = "%s/%s/%s/" % (self.base_url, language, entity)
        header = {
            "Content-Type":"application/json",
            "Authorization":"Token %s" % api_key
        }
        data = {}
        form_data = form.data

        for key in form_data:

            if not form.data[key]:
                continue
            if key in ("person", "organization", "parent", "post", "membership", "member"):
                continue
            elif key == "area":
                if not any(form.data[key].values()):
                    # Because id is a required field
                    continue
            else:
                data[key] = str(form.data[key])

        r = self.session.post(url, headers=header, data=json.dumps(data))
        return r.status_code, r.json()

    def update_entity(self, entity, entity_id, language, api_key, form):
        url = "%s/%s/%s/%s/" % (self.base_url, language, entity, entity_id)
        header = {
            "Content-Type":"application/json",
            "Authorization":"Token %s" % api_key
        }
        data = {}
        for key in form.data:
            # Because we have to hack around the form framework
            if key in ("person", "organization", "parent", "post", "membership", "member"):
                continue
            if key in ("other_names", "contact_details", "identifiers", "links"):
                for item in form.data[key]:
                    print(item["id"])

                    if not item["id"]:
                        del item["id"]
            if key == "area":
                if not form.data[key]:
                    continue
                if not any(form.data[key][0].values()):
                    continue
                data[key] = form.data[key][0]
            
            data[key] = form.data[key]

        r = self.session.put(url, headers=header, data=json.dumps(data))
        print(r.text)
        return r.status_code, r.json()

    def delete_entity(self, entity, entity_id, language, api_key):
        url = "%s/%s/%s/%s/" % (self.base_url, language, entity, entity_id)
        header = {
            "Content-Type":"application/json",
            "Authorization":"Token %s" % api_key
        }
        r = self.session.delete(url, headers=header)

    def list_subitem(self, entity, entity_id, child, language, page, fetch_from_id=True):
        url = "%s/%s/%s/%s/" % (self.base_url, language, entity, entity_id)
        status_code, output = self.get_request(url)
        data = output["result"]
        if not page:
            page = 1
        if not child in data:
            raise ProviderEntityErrorException("Sub Entity not found")
        result = []
        paginator = Paginator(data[child])
        paginated = paginator.return_result(page=page)
        for item in paginated["results"]:

            temp = item
            if fetch_from_id:
                if temp.get("parent_id"):
                    _, parent = self.fetch_entity("organizations", temp["parent_id"], language)
                    temp["parent"] = parent["name"]
                else:
                    temp["parent"] = None

                if temp.get("organization_id"):
                    _, organization = self.fetch_entity("organizations", temp["organization_id"], language)
                    temp["organization"] = organization
                else:
                    temp["organization"] = None

                if temp.get("person_id"):
                    _, person = self.fetch_entity("persons", temp["person_id"], language)
                    temp["person"] = person
                else:
                    temp["person"] = None

                if temp.get("post_id"):
                    _, post = self.fetch_entity("posts", temp["post_id"], language)
                    temp["post"] = post
                else:
                    temp["post"] = None
            result.append(temp)


        paginated["result"] = result
        return status_code, paginated

class Paginator(object):
    def __init__(self, data, page_size=10):
        self.data = data
        self.page_size = page_size
        self.total = len(self.data)
        self.pages = self.total / self.page_size

    def get_page(self, page):
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.data[start:end]

    def return_result(self, page):
        current_page = self.get_page(page)
        results = {}
        results["results"] = current_page
        results["page"] = page
        results["total"] = self.total
        results["per_page"] = self.page_size
        results["num_pages"] = self.pages
        return results



class ProviderEntityNotFoundException(Exception):
    pass


class ProviderEntityErrorException(Exception):
    pass


