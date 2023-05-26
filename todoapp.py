import flet as ft
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Boolean, Identity
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///toDoTasks.sqlite', echo=True)
base = declarative_base()


class TasksDB(base):
    __tablename__ = 'tasks_table'
    task_id = Column(Integer, primary_key = True)
    task_text = Column(String)
    task_status = Column(Boolean)

    def __init__(self, task_text, task_status):
        self.task_text = task_text
        self.task_status = task_status



class Task(ft.UserControl):
    
    def __init__(self, task_text, task_delete, session):
        super().__init__()
        self.task_text = task_text
        self.task_delete = task_delete
        self.session = session
        self.task_id = -1
        self.scaling = 0.82
    
    def build(self):

        self.checkbox = ft.Checkbox(value=False, on_change = self.update_state)
        self.text = ft.Text(value=self.task_text)
        self.edit_field = ft.TextField(expand=0.6)

        self.edit_view = ft.Row(visible=False,
                            alignment="spaceBetween",
                            vertical_alignment="center",
                            controls=[
                                self.edit_field,
                                ft.IconButton(icon=ft.icons.DONE_OUTLINE_OUTLINED,icon_color=ft.colors.GREEN,
                                tooltip="Update To-Do",
                                on_click=self.save_clicked)
                                ]
                            )

        self.edit_btn = ft.IconButton(icon = ft.icons.CREATE_OUTLINED,
                                      tooltip = "Edit To-Do",
                                      scale = self.scaling,
                                      on_click = self.edit_fnc
                                     )
        
        self.remove_btn = ft.IconButton( icon = ft.icons.DELETE_OUTLINED,
                                         tooltip ="Delete To-Do",
                                         scale = self.scaling, 
                                         on_click = self.delete_fnc
                                        )
        
        self.arrow_up_btn = ft.IconButton( icon=ft.icons.ARROW_UPWARD_OUTLINED, 
                                           tooltip ="Move Up", 
                                           scale=self.scaling, 
                                           on_click = self.reorder
                                          )
        
        self.arrow_down_btn = ft.IconButton( icon=ft.icons.ARROW_DOWNWARD_OUTLINED, 
                                             tooltip ="Move Up", 
                                             scale=self.scaling, 
                                             on_click = self.reorder
                                            )
        
        self.container_left = ft.Row(controls=[self.checkbox, self.text])

        self.container_right = ft.Row(spacing = 0, 
                                      controls=[
                                          self.edit_btn, self.remove_btn, 
                                          self.arrow_up_btn, self.arrow_down_btn
                                          ]
                                      )
        
        self.task_wrapper = ft.Row( alignment="spaceBetween", 
                                    vertical_alignment="center", 
                                    controls=[
                                        self.container_left, 
                                        self.container_right
                                        ]
                                    )
        
        
        return ft.Column(controls=[self.task_wrapper,self.edit_view])
    

    def edit_fnc(self, e):
        self.edit_field.value = self.text.value
        self.task_wrapper.visible = False
        self.edit_view.visible = True
        self.update()
    
    # deleting task from the App and DB
    def delete_fnc(self, e):
        session.query(TasksDB).filter(TasksDB.task_id == self.task_id).delete()
        session.commit()
        self.task_delete(self)

    # will be called if text was edited and submitted
    def save_clicked(self, e):
        self.text.value = self.edit_field.value
        self.edit_view.visible = False
        self.task_wrapper.visible = True

        result = session.get(TasksDB, self.task_id)
        if result != None:
            result.task_text = self.text.value
            session.commit()
            self.update()

    # will be called when the task state is changed
    def update_state(self, e):
        result = session.get(TasksDB, self.task_id)
        if result != None:
            result.task_status = self.checkbox.value
            session.commit()
        else:
            print("Task ID nicht gefunden")
    
    def reorder(self):
        raise NotImplementedError




class App(ft.UserControl):

    def __init(self, session):
        self.session = session


    def build(self):

        self.new_task_textfield = ft.TextField(hint_text="Enter Task here...",
                                               expand=True,
                                               on_submit=self.add_clicked
                                               )
        self.tasks = ft.Column() #container for tasks


        return ft.Column(
            width=450,
            controls=[
                # Row 1 -- Headline
                ft.Row([ft.Text(value="Todos", style="headlineMedium")], alignment="center"),
                # Row 2 -- textfeld and button to add a task in a single row
                ft.Row(
                    controls=[
                        self.new_task_textfield,
                        ft.FloatingActionButton(icon=ft.icons.ADD, on_click=self.add_clicked),
                    ],
                ),
                # displays column of tasks when created
                self.tasks,
            ],
        ) 
    
    
    def add_clicked(self, e):

        if self.new_task_textfield.value: #if not empty text

            task = Task(self.new_task_textfield.value, self.task_delete, session)
                      
            #adding task to db and setting task_id primary key as a task attribute to identify tasks by id
            tr = TasksDB(self.new_task_textfield.value, False)
            session.add(tr)
            session.commit()
            task_table_obj = session.query(TasksDB).order_by(TasksDB.task_id.desc()).first()
            task.task_id = task_table_obj.task_id

            #adding tasks to the list
            self.tasks.controls.append(task)    #adds task to column, which is stored as a list
            self.new_task_textfield.value = ""  #change textfield value to empty string ()
            self.new_task_textfield.focus()     
            self.update()


    def task_delete(self, task):
        self.tasks.controls.remove(task)        
        self.update()
    
      
    # add tasks from DB to the application window on startup
    def load_tasks_from_db(self):
        
        result = session.query(TasksDB).filter().all()
        
        for r in result:
            task = Task(r.task_text, self.task_delete, session)
            task.task_id = r.task_id

            self.tasks.controls.append(task)
            self.update()

            task.checkbox.value = r.task_status
            task.update()


def main(page: ft.Page):
    page.title = "ToDo App"
    page.horizontal_alignment = "center"
    page.scroll = "adaptive"
    page.window_width = 500
    page.update()
    app = App(session)
    page.add(app)
    app.load_tasks_from_db()

#db setup, session creation
base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

#starting app
ft.app(target=main)

