__author__ = 'sweemeng'
from flask.views import View
from flask.views import MethodView
from flask import render_template
from flask import request as server_request
from flask import Response
from flask import redirect
from flask import session
from flask_security import login_required
import requests
from forms.base import BaseForm
from forms.membership import MembershipForm
from forms.merge import MergeForm
import json
import const
import cachecontrol
import logging


# POPIT_ENDPOINT =  "http://sinar-malaysia.popit.mysociety.org/api/v0.1"
POPIT_ENDPOINT = const.api_endpoint
SUPPORTED_LANGUAGE = ["ms", "en"]

class BaseView(View):
    POPIT_ENDPOINT =  POPIT_ENDPOINT
    decorators = [login_required]
    def __init__(self, entity, template_name):
        self.template_name = template_name
        self.entity = entity
        self.data = None
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)

    def dispatch_request(self, *args, **kwargs):
        raise NotImplementedError()

    def fetch_entity(self, *args, **kwargs):
        raise NotImplementedError()

    def render_error(self, error_code, content):
        return render_template("error.html", error_code=error_code, content=content)

    def render_template(self, *args, **kwargs):
        return render_template(self.template_name, **kwargs)


class ListView(BaseView):

    def fetch_entity(self, entity, page=0, language_key="en"):
        url = "%s/%s" % (self.POPIT_ENDPOINT, entity)

        headers = { "Accept-Language": language_key }
        if page:
            params = { "page": page }
            r = self.session.get(url, params=params, headers=headers, verify=False)
        else:
            r = self.session.get(url, headers=headers, verify=False)
        return (r.status_code, r.json())

    def dispatch_request(self, *args, **kwargs):
        language = session.get("language", "en")
        status_code, data = self.fetch_entity(self.entity, language_key=language)
        if status_code != 200:
            return self.render_error(status_code, error_code=status_code, content=data)
        return self.render_template(data=data)


class SearchView(ListView):
    def search_entity(self, entity, key, value, page=0, language_key="en"):
        headers = { "Accept-Language": language_key }
        url = "%s/search/%s" % (self.POPIT_ENDPOINT, entity)
        params = { "q": "%s:%s" % (key, value) }
        if page:
            params["page"] = page
        r = self.session.get(url, params=params, headers=headers, verify=False)

        return (r.status_code, r.json())

    def dispatch_request(self, *args, **kwargs):
        language = session.get("language", "en")
        search_key = server_request.args.get("search")
        page = server_request.args.get("page")
        if search_key:
            status_code, data = self.search_entity(self.entity, "name", search_key, page=page)
            if status_code != 200:
                return self.render_error(status_code, error_code=status_code, content=data)
            return self.render_template(data=data, search_key=search_key)

        status_code, data = self.fetch_entity(self.entity, page=page)
        if status_code != 200:
            return self.render_error(status_code, data)
        return self.render_template(data=data)


class CreateView(BaseView):
    methods = ["GET", "POST"]
    def __init__(self, entity, template_name, api_key, form):
        if not issubclass(form, BaseForm):
            raise Exception("Invalid object")
        super(CreateView, self).__init__(entity,template_name)
        self.form = form
        self.headers = { "Content-Type":"application/json", "Apikey":api_key }

    def create_entity(self, form, language_key="en"):
        # Don't think all field comform to popit standard, for example parent field in organization, which is for convenience
        # We only create the mainfield not the subfield.
        url = "%s/%s" % (self.POPIT_ENDPOINT, self.entity)
        data = {}

        form_data = form.data

        for key in form_data:
            if not form.data[key]:
                continue
            elif "id" in key:
                data[key] =  str(form.data[key])
            elif key == "area":
                if not any(form.data[key].values()):
                    # Because id is a required field
                    continue
            elif key in ("organization", "person", "post", "parent"):
                continue
            else:
                data[key] = { language_key: str(form.data[key]) }

        r = self.session.post(url, data=json.dumps(data), headers=self.headers, verify=False)
        return (r.status_code, r.json())

    def dispatch_request(self, *args, **kwargs):

        language = session.get("language", "en")

        if server_request.form:
            form = self.form(server_request.form)

            if form.validate():
                status_code, data = self.create_entity(form, language_key=language)
                if status_code != 200:
                    return self.render_error(error_code=status_code, content=data)
                return redirect("/%s/edit/%s" %(self.entity, data["result"]["id"]))
            else:
                return self.render_template(self.template_name, form=form)
            return redirect("/%s"% self.entity)
        else:
            form = self.form()
        return self.render_template(self.template_name, form=form)


class EditView(BaseView):
    methods = ["GET", "POST"]
    def __init__(self, entity, template_name, api_key, form):
        if not issubclass(form, BaseForm):
            raise Exception("Invalid object")
        super(EditView, self).__init__(entity,template_name)
        self.form = form
        self.headers = { "Content-Type":"application/json", "Apikey":api_key }
        self.data = {}

    def fetch_entity(self, entity, entity_id, language_key="en"):
        self.headers["Accept-Language"] = language_key
        url = "%s/%s/%s" % (self.POPIT_ENDPOINT, entity, entity_id)
        r = self.session.get(url, headers=self.headers, verify=False)

        if r.status_code != 200:
            return r.status_code, r.json()
        data = r.json()["result"]

        for key, value in data.items():
            if "_id" in key:
                if key == "parent_id":
                    if value:
                        status, temp_data = self.fetch_entity("organizations", value, language_key=language_key)

                        if status == 200:
                            data["parent"] = temp_data["result"]["name"]
                else:

                    temp_entity, temp_id = key.split("_")

                    temp_entity = "%ss" % temp_entity
                    status, temp_data = self.fetch_entity(temp_entity, value, language_key=language_key)

                    if "name" in temp_data["result"]:
                        data[temp_entity[:-1]] = temp_data["result"]["name"]
                    else:
                        data[temp_entity[:-1]] = temp_data["result"]["label"]

        return (r.status_code, {"result": data})

    def assemble_data(self, entity, entity_id):
        data = {}
        for language in SUPPORTED_LANGUAGE:
            status_code, temp_data = self.fetch_entity(entity, entity_id, language_key=language)
            for field, value in temp_data["result"].items():
                if field in ("name", "summary", "biography", "description", "label"):
                    temp = data.setdefault(field, {})
                    temp[language] = value

                else:
                    data[field] = value
        return { "result": data }


    def update_entity(self, entity, entity_id, form, original, delete_field=None, language_key="en"):
        updated_data = {}

        original_data = original["result"]

        data = {}

        if delete_field:
            field_delete, field_id = delete_field.split(",")
        else:
            field_delete = None
            field_id = None
        for key in form.data:
            # name is a required field
            if key == "name":

                data[key] = original_data[key]
                data[key][language_key] = form.data[key]
            if key in ("organization", "person", "post"):
                continue

            if key == "area":
                logging.warning(form.data[key])
                if not form.data[key]:
                    continue
                if not any(form.data[key][0].values()):
                    continue

            if type(form.data[key]) is list:

                temp_list = []

                for item in form.data[key]:
                    if key == field_delete:
                        # Skip this one, == delete,
                        if item["id"] == field_id:
                            continue
                    test_list = []
                    new_item = {}
                    for key_ in item:
                        test_list.append(item[key_])
                        if item[key_]:
                            new_item[key_] = item[key_]

                    if any(test_list):
                        temp_list.append(new_item)

                if original_data[key] == temp_list:
                    continue
                else:
                    data[key] = temp_list
                    continue

            if not form.data[key]:
                continue

            if form.data[key] == original_data.get(key):
                continue

            if "id" in key:
                data[key] = form.data[key]
            else:
                if key in ("name", "summary", "biography", "description", "label"):
                    data[key] = original_data[key]
                    data[key][language_key] = form.data[key]
                else:
                    data[key] = form.data[key]


        url = "%s/%s/%s" % (self.POPIT_ENDPOINT, entity, entity_id)

        r = self.session.put(url, data=json.dumps(data), headers=self.headers, verify=False)
        return r.status_code, r.json()

    def clean_form(self, form):
        key_to_pop = []
        for key in form.data:
            if hasattr(form[key], "entries"):
                if not form[key].entries:
                    continue

                if not any(form[key].entries[-1].data.values()):
                    key_to_pop.append(key)
        for key in key_to_pop:
            form[key].pop_entry()
        return form

    def delete_entity(self, entity, entity_id):
        url = "%s/%s/%s" % (self.POPIT_ENDPOINT, entity, entity_id)
        r = self.session.delete(url, headers=self.headers, verify=False)
        return r.status_code, r.json()

    def dispatch_request(self, entity_id):

        language = session.get("language", "en")

        status_code, self.data = self.fetch_entity(self.entity, entity_id, language_key=language)
        if status_code != 200:
            return self.render_error(error_code=status_code, content=self.data)

        form = self.form.from_json(self.data["result"])
        for key in form.data:
            if hasattr(form[key], "entries"):
                form[key].append_entry({})

        if "delete" in server_request.form:
            self.delete_entity(self.entity, entity_id)
            return redirect("/%s" % self.entity)

        if server_request.form:
            form = self.form(server_request.form)
            form = self.clean_form(form)

            delete_field = server_request.form.get("delete_item")
            if form.validate():
                edit_data = self.assemble_data(self.entity, entity_id)
                status_code, data = self.update_entity(self.entity, entity_id, form, edit_data, delete_field, language_key=language)
                if status_code != 200:
                    return self.render_error(error_code=status_code, content=data)
                return redirect("/%s/edit/%s" % (self.entity, entity_id))

        return self.render_template(self.template_name, form=form, data=self.data["result"], edit=True, entity_id=entity_id)


class SearchSubItemView(SearchView):
    def __init__(self, parent_entity, entity, template_name):
        super(SearchSubItemView,self).__init__(entity, template_name)
        self.parent_entity = parent_entity

    def search_entity(self, entity, **kwargs):
        queries = []
        headers = {}
        for key,value in kwargs.items():
            if key == "page":
                continue
            if key == "language_key":
                headers["Accept-Language"] = kwargs["language_key"]
                continue
            queries.append("%s:%s" % (key,value))
        url = "%s/search/%s" % (self.POPIT_ENDPOINT, entity)
        params = { "q": "%".join(queries) }

        if "page" in kwargs:
            params["page"] = kwargs["page"]

        r = self.session.get(url, params=params, headers=headers, verify=False)

        return (r.status_code, r.json())

    def dispatch_request(self, parent_id, *args, **kwargs):
        language = session.get("language", "en")
        search_key = server_request.args.get("search")
        page = server_request.args.get("page")
        id_key = "%s_id" % self.parent_entity[:-1]
        query = {}
        query[id_key] = parent_id
        query["page"] = page
        query["language_key"] = language
        if search_key:

            query["label"] = search_key

            status_code, data = self.search_entity(self.entity, **query)
            if status_code != 200:
                return self.render_error(error_code=status_code, content=data)
            return self.render_template(data=data, search_key=search_key, parent_id=parent_id)

        # Because parent_id do not link back to child and vice versa
        status_code, data = self.search_entity(self.entity, **query)

        return self.render_template(data=data, search_key=search_key, parent_id=parent_id, parent_entity=self.parent_entity)


class CreateSubItemView(CreateView):
    def __init__(self, parent_entity, entity, template_name, api_key, form):
        if not issubclass(form, BaseForm):
            raise Exception("Invalid object")
        super(CreateSubItemView, self).__init__(entity,template_name, api_key, form)
        self.form = form
        self.parent_entity = parent_entity
        self.headers = { "Content-Type":"application/json", "Apikey":api_key }

    def fetch_entity(self, entity, entity_id, language_key="en"):
        self.headers["Accept-Language"] = language_key
        url = "%s/%s/%s" % (self.POPIT_ENDPOINT, entity, entity_id)
        r = self.session.get(url, verify=False)

        return (r.status_code, r.json())

    def dispatch_request(self, parent_id):
        language = session.get("language", "en")
        status_code, data = self.fetch_entity(self.parent_entity, parent_id, language_key=language)
        if status_code != 200:
            return self.render_error(error_code=status_code, content=data)

        parent_key = self.parent_entity[:-1]
        parent_id_key = "%s_id" % parent_key
        init_data = { parent_id_key: parent_id, parent_key: data["result"]["name"]}
        form = self.form.from_json(init_data)
        if server_request.form:

            form = self.form(server_request.form)
            if form.validate():
                status_code, data = self.create_entity(form, language_key=language)
                if status_code != 200:
                    return self.render_error(error_code=status_code, content=data)
            return redirect("/%s" % self.parent_entity)

        return self.render_template(self.template_name, form=form)


# Since this is a special case We might as well just set the parameter
class PostMembershipCreateView(CreateSubItemView):

    def __init__(self, template_name, api_key):
        parent_entity = "posts"
        entity = "memberships"
        form = MembershipForm
        super(PostMembershipCreateView, self).__init__(parent_entity, entity, template_name, api_key, form)

    def dispatch_request(self, parent_id):
        # Only person should be filled manually
        # This should go 2 way
        # 1) add member to a post
        # a) post have their id
        # b) post is linked to an organization
        # 2) via organization
        # a) post is optional
        # b) organization have their id
        status_code, post_data = self.fetch_entity(self.parent_entity, parent_id)
        language = session.get("language", "en")
        if status_code != 200:
            return self.render_error(error_code=status_code, content=post_data)
        # Now post exist
        # Assume post have organization in data
        organization = post_data["result"].get("organization")
        if not organization:
            status_code, org_data = self.fetch_entity("organizations", post_data["result"]["organization_id"])
            if status_code != 200:
                return self.render_error(error_code=status_code, content=org_data)
            organization = org_data["result"]["name"]
        # Now we assemble the data
        form = self.form(
            organization_id=post_data["result"]["organization_id"],
            organization=organization,
            post_id=parent_id,
            post=post_data["result"]["label"]
        )
        if server_request.form:
            form = self.form(server_request.form)
            if form.validate():
                status_code, data = self.create_entity(form)
                if status_code != 200:
                    return self.render_error(error_code=status_code, content=data)
        return self.render_template(self.template_name, form=form, parent_id=parent_id)


class MergePersonView(BaseView):
    methods = ["GET", "POST"]
    def __init__(self, entity, api_key):
        template_name = "merge.html"

        super(MergePersonView, self).__init__(entity,template_name)

        self.headers = { "Content-Type":"application/json", "Apikey":api_key }

    def fetch_entity(self, entity, entity_id, language_key="en"):
        headers = {}
        headers["Accept-Language"] = language_key
        url = "%s/%s/%s" % (self.POPIT_ENDPOINT, entity, entity_id)
        r = self.session.get(url, verify=False)

        return (r.status_code, r.json())

    def dispatch_request(self, *args, **kwargs):
        form = MergeForm()
        if server_request.form:
            form = MergeForm(server_request.form)
            if form.validate():
                target_id = form.target_id.data
                source_id = form.source_id.data

                status_code, source = self.fetch_entity(self.entity, target_id)
                if status_code != 200:
                    return self.render_error(error_code=status_code, content=source)
                status_code, target = self.fetch_entity(self.entity, source_id)

                if status_code != 200:
                    return self.render_error(error_code=status_code, content=source)

                for membership in target["result"]["memberships"]:
                    data = {}
                    try:
                        data["role"] = membership["role"]
                        data["person_id"] = target_id
                        data["organization_id"] = membership["organization_id"]
                        if "post_id" in membership:
                            data["post_id"] = membership["post_id"]
                        data["start_date"] = membership["start_date"]
                        if "end_data" in membership:
                            data["end_date"] = membership["end_date"]
                    except Exception as e:
                        print "attempting to merge: ", membership
                        print e.message
                        return self.render_error("500", content='{"Error":"%s"}' % e.message)

                    url = "%s/%s" % (POPIT_ENDPOINT, "memberships")
                    r = requests.post(url, headers=self.headers, data=json.dumps(data), verify=False)
                    if r.status_code != 200:
                        return self.render_error(error_code=r.status_code, content=r.json())

        return self.render_template(self.template_name, form=form)



class SearchAjaxView(MethodView):
    POPIT_ENDPOINT =  POPIT_ENDPOINT
    def get(self, entity):

        language = session.get("language", "en")
        label = server_request.args.get("label")
        if not label:
            name = server_request.args.get("name")
            status_code, data = self.fetch_entity(entity, "name", name, language_key=language)
        else:
            status_code, data = self.fetch_entity(entity, "label", label, language_key=language)
        return Response(json.dumps(data["result"]), mimetype="application/json")


    def fetch_entity(self, entity, key, value, language_key="en"):
        url = "%s/search/%s" % (self.POPIT_ENDPOINT, entity)
        params = { "q": "%s:%s" % (key, value) }

        headers = { "Accept-Language":language_key}
        r = requests.get(url, params=params, headers=headers, verify=False)

        return (r.status_code, r.json())
