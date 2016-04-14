__author__ = 'sweemeng'
from flask.views import View
from flask.views import MethodView
from flask import render_template
from flask import request as server_request
from flask import Response
from flask import redirect
from flask import session
from flask_security import login_required
from flask_security import roles_required
import requests
from forms.base import BaseForm
from forms.membership import MembershipForm
from forms.merge import MergeForm
from forms.citations import CitationForm
import json
import const
import cachecontrol
import logging
from provider import PopitNgProvider
from provider import Paginator


POPIT_ENDPOINT = const.api_endpoint
SUPPORTED_LANGUAGE = ["ms", "en"]

class BaseView(View):
    decorators = [ roles_required("admin") ]
    def __init__(self, entity, template_name):
        self.template_name = template_name
        self.entity = entity
        self.data = None
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)
        self.provider = PopitNgProvider()

    def dispatch_request(self, *args, **kwargs):
        raise NotImplementedError()

    def render_error(self, error_code, content):
        return render_template("error.html", error_code=error_code, content=content)

    def render_template(self, *args, **kwargs):
        return render_template(self.template_name, **kwargs)


class SingleItemView(BaseView):
    decorators = []
    
    def dispatch_request(self, entity_id):
        language = session.get("language", "en")
        status_code, data = self.provider.fetch_entity(self.entity, entity_id, language)
        if status_code != 200:
            return self.render_error(error_code=status_code, content=data)
        return self.render_template(data=data, entity_id=entity_id)


class ListView(BaseView):
    decorators = []
    edit = False

    def dispatch_request(self, *args, **kwargs):
        language = session.get("language", "en")
        page = server_request.args.get("page")
        status_code, data = self.provider.fetch_entities(self.entity, language, page=page)
        if status_code != 200:
            return self.render_error(error_code=status_code, content=data)
        logging.warn(type(data["total"]))
        return self.render_template(data=data, edit=self.edit)


class ListEditView(BaseView):
    decorators = [ roles_required("admin") ]
    edit = True


class SearchView(ListView):
    decorators = []
    edit = False

    def dispatch_request(self, *args, **kwargs):
        language = session.get("language", "en")
        search_key = server_request.args.get("search")
        page = server_request.args.get("page")
        if search_key:
            status_code, data = self.provider.search_entities(
                self.entity, language, page=page, search_params={"name": search_key}
            )
            if status_code != 200:
                return self.render_error(error_code=status_code, content=data)
            return self.render_template(data=data, search_key=search_key, edit=self.edit)

        status_code, data = self.provider.fetch_entities(self.entity, language, page=page)
        if status_code != 200:
            return self.render_error(status_code, data)
        return self.render_template(self.template_name, data=data, edit=self.edit)


class SearchEditView(SearchView):
    decorators = [ roles_required("admin") ]
    edit = True


class CreateView(BaseView):
    methods = ["GET", "POST"]
    def __init__(self, entity, template_name, api_key, form):
        if not issubclass(form, BaseForm):
            raise Exception("Invalid object")
        super(CreateView, self).__init__(entity,template_name)
        self.form = form
        self.headers = { "Content-Type":"application/json", "Apikey":api_key }
        self.api_key = api_key

    def dispatch_request(self, *args, **kwargs):

        language = session.get("language", "en")

        if server_request.form:
            form = self.form(server_request.form)

            if form.validate():
                status_code, data = self.provider.create_entity(
                    self.entity, 
                    language,
                    self.api_key, 
                    form)
                if status_code != 201:
                    return self.render_error(error_code=status_code, content=data)
                return redirect("/%s/edit/%s" %(self.entity, data["result"]["id"]))
            else:
                return self.render_template(self.template_name, form=form)
        else:
            form = self.form()
        return self.render_template(self.template_name, form=form, edit=True)


class EditView(BaseView):
    methods = ["GET", "POST"]
    def __init__(self, entity, template_name, api_key, form):
        if not issubclass(form, BaseForm):
            raise Exception("Invalid object")
        super(EditView, self).__init__(entity,template_name)
        self.form = form
        self.headers = { "Content-Type":"application/json", "Apikey":api_key }
        self.data = {}
        self.api_key = api_key

    def assemble_data(self, entity, entity_id):
        data = {}
        for language in SUPPORTED_LANGUAGE:
            status_code, temp_data = self.provider.fetch_entity(entity, entity_id, language)
            for field, value in temp_data["r     esult"].items():
                if field in ("name", "summary", "description", "label"):
                    temp = data.setdefault(field, {})
                    temp[language] = value

                else:
                    data[field] = value
        return { "result": data }


    def clean_form(self, form):
        key_to_pop = []
        for key in form.data:
            if key == "area":
                continue
            if hasattr(form[key], "entries"):
                if not form[key].entries:
                    continue

                if not any(form[key].entries[-1].data.values()):
                    key_to_pop.append(key)
        for key in key_to_pop:
            form[key].pop_entry()
        return form

    def dispatch_request(self, entity_id):

        language = session.get("language", "en")

        status_code, self.data = self.provider.fetch_entity(self.entity, entity_id, language)
        if status_code != 200:
            return self.render_error(error_code=status_code, content=self.data)

        form = self.form.from_json(self.data)

        for key in form.data:
            if key == "area":
                continue
            if hasattr(form[key], "entries"):
                form[key].append_entry({})

        # TODO: check for type
        if "delete" in server_request.form:
            if self.entity == "memberships":
                if self.data.get("post_id"):
                    redirect_url = "/posts/%s/memberships/edit" % self.data["post_id"]
                else:
                    redirect_url = "/organizations/%s/memberships/edit" % self.data["organization_id"]
            else:
                redirect_url = "/%s" % self.entity
            self.provider.delete_entity(self.entity, entity_id, language, self.api_key)
            return redirect(redirect_url)

        if "delete_item" in server_request.form:
            redirect_url = "/%s/edit/%s" % (self.entity, entity_id)
            item, item_id = server_request.form["delete_item"].split(",")
            self.provider.delete_subitem(self.entity, entity_id, item, item_id, language, self.api_key)
            return redirect(redirect_url)

        if server_request.form:
            form = self.form(server_request.form)
            form = self.clean_form(form)

            if form.validate():

                status_code, data = self.provider.update_entity(
                    self.entity, 
                    entity_id, language, self.api_key, form)
                if status_code != 200:
                    logging.warn(data)
                    return self.render_error(error_code=status_code, content=data)
                return redirect("/%s/edit/%s" % (self.entity, entity_id))

        return self.render_template(self.template_name, form=form, data=self.data, edit=True, entity_id=entity_id)


class SearchSubItemView(SearchView):
    decorators = []
    edit = False
    def __init__(self, parent_entity, entity, template_name):
        super(SearchSubItemView,self).__init__(entity, template_name)
        self.parent_entity = parent_entity

    def dispatch_request(self, parent_id, *args, **kwargs):
        language = session.get("language", "en")
        search_key = server_request.args.get("search")
        page = server_request.args.get("page")
        id_key = "%s_id" % self.parent_entity[:-1]
        query = {}
        query[id_key] = parent_id
        if search_key:

            query["label"] = search_key

            status_code, data = self.provider.search_entities(
                 self.entity,
                 language,
                 page=page,
                 search_params=query
            )
            if status_code != 200:
                return self.render_error(error_code=status_code, content=data)
            return self.render_template(data=data, search_key=search_key, parent_id=parent_id, edit=self.edit,
                                        parent_entity=self.parent_entity)

        # Because parent_id do not link back to child and vice versa

        status_code, data = self.provider.list_subitem(
            self.parent_entity,
            parent_id,
            self.entity,
            language,
            page
        )
        print(data)
        return self.render_template(data=data, search_key=search_key, parent_id=parent_id, parent_entity=self.parent_entity,
                                    edit=self.edit)


class SearchSubItemEditView(SearchSubItemView):
    decorators = [ roles_required("admin") ]
    edit = True


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

    def dispatch_request(self, parent_id):
        language = session.get("language", "en")
        status_code, data = self.provider.fetch_entity(self.parent_entity, parent_id, language)
        if status_code != 200:
            return self.render_error(error_code=status_code, content=data)

        parent_key = self.parent_entity[:-1]
        parent_id_key = "%s_id" % parent_key
        init_data = { parent_id_key: parent_id, parent_key: data["name"]}
        form = self.form.from_json(init_data)
        form["area"].append_entry({})

        if server_request.form:

            form = self.form(server_request.form)
            form = self.clean_form(form)
            if form.validate():
                status_code, data = self.provider.create_entity(self.entity, language, self.api_key, form)
                if status_code != 201:
                    return self.render_error(error_code=status_code, content=data)
                return redirect("/%s/%s/%s/edit" % (self.parent_entity, parent_id, self.entity))
            return redirect("/%s/%s/%s/edit" % (self.parent_entity, parent_id, self.entity))

        return self.render_template(self.template_name, form=form, edit=True)


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
        language = session.get("language", "en")
        status_code, post_data = self.provider.fetch_entity(self.parent_entity, parent_id, language)

        if status_code != 200:
            return self.render_error(error_code=status_code, content=post_data)
        # Now post exist
        # Assume post have organization in data
        print(post_data)
        organization = post_data.get("organization")
        if not organization:
            status_code, org_data = self.provider.fetch_entity("organizations", post_data["organization_id"], language=language)
            if status_code != 200:
                return self.render_error(error_code=status_code, content=org_data)
            organization = org_data["name"]
        # Now we assemble the data
        form = self.form(
            organization_id=post_data["organization_id"],
            organization=organization,
            post_id=parent_id,
            post=post_data["label"]
        )
        if server_request.form:
            form = self.form(server_request.form)
            if form.validate():
                status_code, data = self.provider.create_entity(
                    self.entity, language, self.api_key, form
                )
                if status_code != 201:
                    return self.render_error(error_code=status_code, content=data)
                return redirect("/%s/%s/%s" % (self.parent_entity, parent_id, self.entity))
        return self.render_template(self.template_name, form=form, parent_id=parent_id, edit=True)


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

                for membership in target["memberships"]:
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

        return self.render_template(self.template_name, form=form, edit=True)



class SearchAjaxView(MethodView):
    POPIT_ENDPOINT =  POPIT_ENDPOINT
    def get(self, entity):

        language = session.get("language", "en")

        provider = PopitNgProvider()

        label = server_request.args.get("label")
        if not label:
            name = server_request.args.get("name")

            status_code, data = provider.search_entities(
                entity,
                language,
                search_params={"name":name}
            )
        else:
            status_code, data = provider.search_entities(
                entity,
                language,
                search_params={"label":label}
            )
        return Response(json.dumps(data["results"]), mimetype="application/json")


# TODO: implement views based show citation list
# TODO: link to open new window/tab target="_blank"
# TODO: each delete shows the full link
# TODO: the entity is different than the rest'
# TODO: check for parent item(the item the citation belong to) existence
class CitationView(View):

    def __init__(self, entity):
        self.entity = entity
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)
        self.provider = PopitNgProvider()
        self.form = CitationForm

    def dispatch_request(self, entity_id, field):
        language = session.get("language", "en")

        status_code, entity = self.provider.fetch_entity(self.entity, entity_id, language)
        data={}
        status_code, output = self.provider.fetch_item_citation(self.entity, entity_id, field, language)
        if status_code != 200:
            return render_template("error.html", error_code=status_code, content=data)
        data["citations"] = output

        if entity.get("name"):
            data["name"] = entity["name"]

        elif entity.get("identifier"):
            data["name"] = entity["identifier"]

        else:
            data["name"] = entity["label"]

        return render_template("citations_view.html", data=data)



class CitationEditView(View):
    methods = ["GET", "POST"]
    decorators = [roles_required("admin")]

    def __init__(self, entity, api_key):
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)
        self.provider = PopitNgProvider()
        self.entity = entity
        self.api_key = api_key

    def process_form(self, citation, entity_id, field, language):
        if citation["id"]:
            status_code, output = self.provider.update_item_citation(
                self.entity, entity_id, field, citation["id"], language, self.api_key, citation)
        else:
            status_code, output = self.provider.create_item_citation(
                self.entity, entity_id, field, language, self.api_key, citation)
        return status_code, output

    def dispatch_request(self, entity_id, field):
        language = session.get("language", "en")

        status_code, entity = self.provider.fetch_entity(self.entity, entity_id, language)
        data = {}
        status_code, output = self.provider.fetch_item_citation(self.entity, entity_id, field, language)

        if status_code != 200:
            return render_template("error.html", error_code=status_code, content=data)

        data["citations"] = output
        form = CitationForm.from_json(data)
        form["citations"].append_entry({})
        if entity.get("name"):
            data["name"] = entity["name"]

        elif entity.get("identifier"):
            data["name"] = entity["identifier"]

        else:
            data["name"] = entity["label"]

        if "delete_item" in server_request.form:

            key = server_request.form["delete_item"].split(",")[1]
            status_code = self.provider.delete_item_citation(
                self.entity, entity_id, field, key, language, self.api_key
            )
            print(status_code, entity)
            redirect_url = "/%s/%s/citations/%s/edit" % (self.entity, entity_id, field)
            return redirect(redirect_url)

        if server_request.form:
            form = CitationForm(server_request.form)
            if form.validate():

                for citation in form.data["citations"]:
                    if not citation["url"]:
                        continue

                    status_code, output = self.process_form(
                        citation, entity_id, field, language
                    )
                    print(status_code, output)
                    if status_code != 200 and status_code != 201:

                        return render_template("error.html", error_code=status_code, content=citation)

                redirect_url = "/%s/%s/citations/%s/edit" % (self.entity, entity_id, field)
                return redirect(redirect_url)

        return render_template("citations.html", form=form, data=data)



class SubItemCitationView(View):

    def __init__(self, parent_entity, child_entity):
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)
        self.provider = PopitNgProvider()
        self.parent_entity = parent_entity
        self.child_entity = child_entity

    def dispatch_request(self, parent_id, child_id, field):
        language = session.get("language", "en")
        data = {}
        status, entity = self.provider.fetch_subitem(self.parent_entity, parent_id, self.child_entity, child_id, language)
        if status != 200:
            return render_template("error.html", error_code=status, content=entity)

        if entity.get("name"):
            data["name"] = entity["name"]

        elif entity.get("identifier"):
            data["name"] = entity["identifier"]

        else:
            data["name"] = entity["label"]

        status_code, output = self.provider.fetch_subitem_citation(
            self.parent_entity,
            parent_id,
            self.child_entity,
            child_id,
            field,
            language
        )

        if status_code != 200:
            return render_template("error.html", error_code=status_code, content=output)
        data["citations"] = output

        return render_template("citations_view.html", data=data)


class SubItemEditCitationView(View):
    decorators = [roles_required("admin")]

    methods = ["GET", "POST"]

    def __init__(self, parent_entity, child_entity, api_key):
        session = requests.Session()
        self.session = cachecontrol.CacheControl(session)
        self.provider = PopitNgProvider()

        self.parent_entity = parent_entity
        self.child_entity = child_entity
        self.api_key = api_key

    def process_form(self, citation, parent_id, child_id, field, language):
        if citation["id"]:
            status_code, output = self.provider.update_subitem_citation(
                self.parent_entity,
                parent_id,
                self.child_entity,
                child_id,
                field,
                citation["id"],
                language,
                self.api_key,
                citation
            )
        else:
            status_code, output = self.provider.create_subitem_citation(
                self.parent_entity,
                parent_id,
                self.child_entity,
                child_id,
                field,
                language,
                self.api_key,
                citation
            )
        return status_code, output

    def dispatch_request(self, parent_id, child_id, field):

        language = session.get("language", "en")
        data = {}
        status, entity = self.provider.fetch_subitem(self.parent_entity, parent_id, self.child_entity, child_id,
                                                     language)
        if status != 200:
            return render_template("error.html", error_code=status, content=entity)

        status_code, output = self.provider.fetch_subitem_citation(
            self.parent_entity,
            parent_id,
            self.child_entity,
            child_id,
            field,
            language
        )
        print(output)
        data["citations"] = output
        print(data)
        form = CitationForm.from_json(data)
        form["citations"].append_entry({})
        print(form["citations"])

        if entity.get("name"):
            data["name"] = entity["name"]

        elif entity.get("identifier"):
            data["name"] = entity["identifier"]

        else:
            data["name"] = entity["label"]

        if "delete_item" in server_request.form:
            key = server_request.form["delete_item"].split(",")[1]
            self.provider.delete_subitem_citation(self.parent_entity,
                                                  parent_id,
                                                  self.child_entity,
                                                  child_id, field, key, language, self.api_key)

            redirect_url = "/%s/%s/%s/%s/citations/%s/edit" % (self.parent_entity, parent_id, self.child_entity, child_id, field)
            return redirect(redirect_url)

        if server_request.form:
            form = CitationForm(server_request.form)
            if form.validate():
                for citation in form.data["citations"]:
                    if not citation["url"]:
                        continue
                    status_code, output = self.process_form(citation, parent_id, child_id, field, language)
                    print(status_code, output)
                    if status_code != 200 and status_code != 201:
                        return render_template("error.html", error_code=status_code, content=citation)

                redirect_url = "/%s/%s/%s/%s/citations/%s/edit" % (self.parent_entity, parent_id, self.child_entity, child_id, field)
                return redirect(redirect_url)

        return render_template("citations.html", form=form, data=data)
