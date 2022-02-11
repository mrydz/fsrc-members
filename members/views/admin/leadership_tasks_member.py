'''
leadership_tasks_member - member task handling
===========================================
'''

# standard
from datetime import date

# pypi
from flask import g, current_app, request, url_for
from flask_security import current_user
from markdown import markdown
from dominate.tags import a, div, input, button

# homegrown
from . import bp
from ...model import db, LocalInterest, LocalUser, Task, Files, InputFieldData
from ...model import FIELDNAME_ARG, NEED_ONE_OF, NEED_REQUIRED, INPUT_TYPE_UPLOAD, INPUT_TYPE_DISPLAY
from ...version import __docversion__
from loutilities.tables import SEPARATOR, get_request_data
from loutilities.filters import filtercontainerdiv, filterdiv
from loutilities.user.roles import ROLE_SUPER_ADMIN, ROLE_LEADERSHIP_ADMIN, ROLE_LEADERSHIP_MEMBER
from loutilities.user.tables import DbCrudApiInterestsRolePermissions
from loutilities.user.tablefiles import FieldUpload
from .viewhelpers import lastcompleted, get_status, get_order, get_expires
from .viewhelpers import create_taskcompletion, get_task_completion, get_member_tasks

debug = False

adminguide = 'https://members.readthedocs.io/en/{docversion}/leadership-task-member-guide.html'.format(docversion=__docversion__)

# field upload endpoint
fieldupload = FieldUpload(
                app=bp,  # use blueprint instead of app
                db=db,
                local_interest_model=LocalInterest,
                roles_accepted=[ROLE_SUPER_ADMIN, ROLE_LEADERSHIP_ADMIN, ROLE_LEADERSHIP_MEMBER],
                uploadendpoint='admin.fieldupload',
                endpointvalues={'interest': '<interest>'},
                uploadrule='/<interest>/fieldupload',
                fieldname = lambda: request.args.get(FIELDNAME_ARG),
                filesdirectory=lambda: current_app.config['APP_FILE_FOLDER'],
                localinterestmodel=LocalInterest,
                filesmodel=Files
            )
fieldupload.register()

def mdrow(dbrow):
    if dbrow.description:
        return markdown(dbrow.description, extensions=['md_in_html', 'attr_list'])
    else:
        return ''

def get_options(f):
    if not f.fieldoptions:
        return []
    else:
        return f.fieldoptions.split(SEPARATOR)

def addlfields(task):
    taskfields = []
    tc = get_task_completion(task, current_user)

    for ttf in task.fields:
        f = ttf.taskfield
        thistaskfield = {}
        for key in 'taskfield,fieldname,displaylabel,displayvalue,inputtype,fieldinfo,priority,uploadurl'.split(','):
            thistaskfield[key] = getattr(f, key)
            # displayvalue gets markdown translation
            if key == 'displayvalue' and getattr(f, key):
                thistaskfield[key] = markdown(getattr(f, key), extensions=['md_in_html', 'attr_list'])
        thistaskfield['fieldoptions'] = get_options(f)


        if tc:
            # field may exist now but maybe didn't before
            field = InputFieldData.query.filter_by(field=f, taskcompletion=tc).one_or_none()

            # field was found
            if field:
                value = field.value
                if f.inputtype != INPUT_TYPE_UPLOAD:
                    thistaskfield['value'] = value
                else:
                    file = Files.query.filter_by(fileid=value).one()
                    thistaskfield['value'] = a(file.filename,
                                               href=url_for('admin.file',
                                                            interest=g.interest,
                                                            fileid=value),
                                               target='_blank').render()

            # field wasn't found
            else:
                thistaskfield['value'] = None

        taskfields.append(thistaskfield)
    return taskfields

def taskchecklist_pretablehtml():
    pretablehtml = div()
    with pretablehtml:
        # hide / show hidden rows
        with filtercontainerdiv(style='margin-bottom: 4px;'):
            datefilter = filterdiv('positiondate-external-filter-startdate', 'In Position On')

            with datefilter:
                input(type='text', id='effective-date', name='effective-date' )
                button('Today', id='todays-date-button')

    return pretablehtml.render()

taskchecklist_dbattrs = 'id,task,description,priority,__readonly__,__readonly__,__readonly__,__readonly__,__readonly__'.split(',')
taskchecklist_formfields = 'rowid,task,description,priority,lastcompleted,addlfields,status,order,expires'.split(',')
taskchecklist_dbmapping = dict(zip(taskchecklist_dbattrs, taskchecklist_formfields))
taskchecklist_formmapping = dict(zip(taskchecklist_formfields, taskchecklist_dbattrs))

taskchecklist_formmapping['description'] = mdrow
taskchecklist_formmapping['addlfields'] = addlfields
taskchecklist_formmapping['lastcompleted'] = lambda task: lastcompleted(task, current_user)
taskchecklist_formmapping['status'] = lambda task: get_status(task, current_user)
taskchecklist_formmapping['order'] = lambda task: get_order(task, current_user)
taskchecklist_formmapping['expires'] = lambda task: get_expires(task, current_user)

class TaskChecklist(DbCrudApiInterestsRolePermissions):
    def __init__(self, **kwargs):
        
        self.kwargs = kwargs
        args = dict(
            app=bp,  # use blueprint instead of app
            db=db,
            model=Task,
            local_interest_model=LocalInterest,
            roles_accepted=[ROLE_SUPER_ADMIN, ROLE_LEADERSHIP_ADMIN, ROLE_LEADERSHIP_MEMBER],
            template='datatables.jinja2',
            templateargs={'adminguide': adminguide},
            pagename='Task Checklist',
            endpoint='admin.taskchecklist',
            endpointvalues={'interest': '<interest>'},
            rule='/<interest>/taskchecklist',
            dbmapping=taskchecklist_dbmapping,
            formmapping=taskchecklist_formmapping,
            pretablehtml=taskchecklist_pretablehtml,
            validate = self._validate,
            clientcolumns=[
                {'data': '',  # needs to be '' else get exception converting options from meetings render_template
                 # TypeError: '<' not supported between instances of 'str' and 'NoneType'
                 'name': 'view-task',
                 'className': 'view-task shrink-to-fit',
                 'orderable': False,
                 'defaultContent': '',
                 'label': '',
                 'type': 'hidden',  # only affects editor modal
                 'title': 'View',
                 'render': {'eval': 'render_icon("fas fa-eye")'},
                 },
                {'data': 'order', 'name': 'order', 'label': 'Display Order',
                 'type':'hidden',
                 'className': 'Hidden',
                 },
                {'data': 'priority', 'name': 'priority', 'label': 'Priority',
                 'type':'hidden',
                 'className': 'Hidden',
                 },
                {'data': 'task', 'name': 'task', 'label': 'Task',
                 'type': 'display',
                 'orderable': False,
                 'className': 'editorFullWidthField task_bold',
                 },
                {'data': 'description', 'name': 'description', 'label': '',
                 'type': 'display',
                 'className': 'editorFullWidthField',
                 'edonly': True,
                 },
                {'data': 'status', 'name': 'status', 'label': 'Status',
                 'orderable': False,
                 'type': 'readonly',
                 'className': 'status-field',
                 },
                {'data': 'lastcompleted', 'name': 'lastcompleted', 'label': 'Last Completed',
                 'orderable': False,
                 'type': 'readonly',
                 },
                {'data': 'expires', 'name': 'expires', 'label': 'Expiration Date',
                 'orderable': False,
                 'type': 'readonly',
                 'className': 'status-field',
                 },
            ],
            servercolumns=None,  # not server side
            idSrc='rowid',
            buttons=[
                {
                    'extend':'edit',
                    'name': 'view-task',
                    'text':'View Task',
                    'editor': {'eval':'editor'},
                    'className': 'Hidden',
                }
            ],
            dtoptions={
                'scrollCollapse': True,
                'scrollX': True,
                'scrollXInner': "100%",
                'scrollY': True,
                'rowCallback': {'eval': 'set_cell_status_class'},
                'order': [['order:name', 'asc'], ['expires:name', 'asc'], ['priority:name', 'asc']],
                'lengthMenu': [10, 25, 50, 100],
                'pageLength': 25,
            },
            edoptions={
                'i18n': {
                    'edit' :
                         {
                             'title'  : 'Task',
                             'submit' : 'Mark Complete'
                         }
                },
                'formOptions': {
                    'main': {
                        'focus': None
                    }
                },
            }
        )
        args.update(kwargs)
        super().__init__(**args)

    def open(self):
        theserows = []

        # collect all the tasks to send to client
        member = self._get_localuser()

        # collect all the tasks which are referenced by positions and taskgroups for this member
        ondate = request.args.get('ondate', date.today())
        tasks = get_member_tasks(member, ondate)

        for task in iter(tasks):
            theserows.append(task)

        self.rows = iter(theserows)

    def updaterow(self, thisid, formdata):
        # find the task and local user
        thistask = Task.query.filter_by(id=thisid).one()
        localuser = self._get_localuser()

        create_taskcompletion(thistask, localuser, self.localinterest, formdata)

        # TODO: need to add completion date, or status, or display class to the tasks returned
        return self.dte.get_response_data(thistask)

    def _get_localuser(self):
        # TODO: process request.args to see if different user is needed
        return LocalUser.query.filter_by(user_id=current_user.id, **self.queryparams).one()

    def _validate(self, action, formdata):
        results = []

        # kludge to get task.id
        # NOTE: this is only called from 'edit' / put function, and there will be only one id
        thisid = list(get_request_data(request.form).keys())[0]
        thistask = Task.query.filter_by(id=thisid).one()

        # build lists of required and shared fields
        required = []
        one_of = []
        override_completion = []
        for tasktaskfield in thistask.fields:
            taskfield = tasktaskfield.taskfield
            # ignore display-only fields
            if taskfield.inputtype == INPUT_TYPE_DISPLAY:
                continue
            if tasktaskfield.need == NEED_REQUIRED:
                required.append(taskfield.fieldname)
            elif tasktaskfield.need == NEED_ONE_OF:
                one_of.append(taskfield.fieldname)
            if taskfield.override_completion:
                override_completion.append(taskfield.fieldname)

        # verify required fields were supplied
        for field in required:
            if not formdata[field]:
                results.append({'name': field, 'status': 'please supply'})

        # verify one of the one_of fields was supplied
        onefound = False
        for field in one_of:
            if formdata[field]:
                onefound = True
        if not onefound:
            for field in one_of:
                results.append({'name':field, 'status': 'one of these must be supplied'})

        # verify fields which override completion date (should only be one if configured properly)
        for field in override_completion:
            if formdata[field] > date.today().isoformat():
                results.append({'name':field, 'status': 'cannot specify date later than today'})

        return results


taskchecklist_view = TaskChecklist()
taskchecklist_view.register()

