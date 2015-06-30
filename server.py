__author__ = 'sweemeng'
from views import SearchView
from views import EditView
from views import CreateView
from views import SearchAjaxView
from views import SearchSubItemView
from views import CreateSubItemView
from views import PostMembershipCreateView
from flask import session
from flask import request
from flask import redirect
from flask.sessions import SessionInterface
from flask_login import LoginManager
from flask.ext.security import Security, SQLAlchemyUserDatastore, login_required
from forms.organization import OrganizationEditForms
from forms.organization import OrganizationForms
from forms.posts import PostEditForm
from forms.posts import PostForm
from forms.membership import MembershipForm
from forms.membership import MembershipEditForm
from forms.person import PersonForm
from forms.person import PersonEditForm
from beaker.middleware import SessionMiddleware
import logging
import const
from app import app
from db import User
from db import Role
from app import db




api_key= const.api_key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


app.add_url_rule('/organizations', view_func=SearchView.as_view("organizations", entity="organizations",
                                                                template_name="organizations.html"))
app.add_url_rule('/organizations/edit/<entity_id>', view_func=EditView.as_view("organization_edit",
                                                                                  entity="organizations",
                                                                                  template_name="organization.html",
                                                                                  api_key=api_key,
                                                                                  form=OrganizationEditForms))
app.add_url_rule('/organizations/create', view_func=CreateView.as_view("organization_create",
                                                                       entity="organizations",
                                                                       template_name="organization.html",
                                                                       api_key=api_key,
                                                                       form=OrganizationForms))
app.add_url_rule('/organizations/<parent_id>/posts', view_func=SearchSubItemView.as_view("posts",
                                                                                           parent_entity="organizations",
                                                                                           entity="posts",
                                                                                           template_name="posts.html"))

app.add_url_rule('/posts/edit/<entity_id>', view_func=EditView.as_view("posts_edit",
                                                                       entity="posts",
                                                                       template_name="post.html",
                                                                       api_key=api_key,
                                                                       form=PostEditForm))

app.add_url_rule('/organizations/<parent_id>/posts/create', view_func=CreateSubItemView.as_view("posts_create",
                                                                                                parent_entity="organizations",
                                                                                                entity="posts",
                                                                                                template_name="post.html",
                                                                                                api_key=api_key,
                                                                                                form=PostForm
                                                                                                ))

app.add_url_rule('/posts/<parent_id>/memberships', view_func=SearchSubItemView.as_view("post_membership_list",
                                                                                           parent_entity="posts",
                                                                                           entity="memberships",
                                                                                           template_name="memberships.html"))

app.add_url_rule('/organizations/<parent_id>/memberships', view_func=SearchSubItemView.as_view("organizations_membership_list",
                                                                                           parent_entity="organizations",
                                                                                           entity="memberships",
                                                                                           template_name="memberships.html"))

app.add_url_rule('/posts/<parent_id>/memberships/create', view_func=PostMembershipCreateView.as_view("post_membership_create",
                                                                                                     template_name="membership.html",
                                                                                                     api_key=api_key
                                                                                                     ))

app.add_url_rule('/organizations/<parent_id>/memberships/create', view_func=CreateSubItemView.as_view("organization_membership_create",
                                                                                                      parent_entity="organizations",
                                                                                                      entity="memberships",
                                                                                                      template_name="membership.html",
                                                                                                      api_key=api_key,
                                                                                                      form=MembershipForm))

app.add_url_rule('/memberships/edit/<entity_id>', view_func=EditView.as_view("membership_edit",
                                                                             entity="memberships",
                                                                             template_name="membership.html",
                                                                             api_key=api_key,
                                                                             form=MembershipEditForm))

app.add_url_rule('/persons', view_func=SearchView.as_view("persons", entity="persons",
                                                                template_name="persons.html"))
app.add_url_rule('/persons/edit/<entity_id>', view_func=EditView.as_view("person_edit",
                                                                                  entity="persons",
                                                                                  template_name="person.html",
                                                                                  api_key=api_key,
                                                                                  form=PersonEditForm))
app.add_url_rule('/persons/create', view_func=CreateView.as_view("person_create",
                                                                       entity="persons",
                                                                       template_name="person.html",
                                                                       api_key=api_key,
                                                                       form=PersonForm))



app.add_url_rule('/search/<entity>', view_func=SearchAjaxView.as_view("search"))

app.add_url_rule('/persons/<parent_id>/memberships/create', view_func=CreateSubItemView.as_view("persons_membership_create",
                                                                                                      parent_entity="persons",
                                                                                                      entity="memberships",
                                                                                                      template_name="membership.html",
                                                                                                      api_key=api_key,
                                                                                                      form=MembershipForm))

app.add_url_rule('/persons/<parent_id>/memberships', view_func=SearchSubItemView.as_view("persons_membership_list",
                                                                                           parent_entity="persons",
                                                                                           entity="memberships",
                                                                                           template_name="memberships.html"))

session_opts = {
    "session.type": "cookie",
    "session.validate_key": "sinar.popit.editor"
}


class BeakerSessionInterface(SessionInterface):
    def open_session(self, app, request):
        session = request.environ["beaker.session"]
        return session

    def save_session(self, app, session, response):
        session.save()


@app.route("/language/set/<language_code>")
def set_language(language_code):
    if language_code not in ("ms", "en"):
        session["language"] = "en"
    session["language"] = language_code
    logging.warning(session)
    return redirect(request.referrer)

@app.route("/logged_in")
@login_required
def logged_in():
    return "logged in"

@app.before_first_request
def create_user():
    db.create_all()
    if not user_datastore.find_user(email=const.admin_name):
        user_datastore.create_user(email=const.admin_name, password=const.admin_pass)
        db.session.commit()



if __name__ == "__main__":
    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()
    app.run(host="0.0.0.0", debug=True, port=9000)