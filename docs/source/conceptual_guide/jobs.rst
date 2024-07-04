.. _jobs:

Jobs and job queue
==================

Some processes in the field of machine learning, such as model training, take a long time (several minutes or hours). During this time, the CPU is
used to its maximum capacity, preventing any process from using it until the job is finished.

On the other hand, **DashAI** is a software with 3 layers:

* Backend, in charge of the business logic, that is, the place where all the processes are carried out.
* Frontend, in charge of visualization and communication with the user.
* API, in charge of transporting data between the other two layers.

When the frontend sends data to the backend, the API processes the request and performs any necessary procedures.
If the backend is processing a request, the API cannot process any further requests and the application freezes until the procedure is completed.

If we combine this last problem with the time it takes for a process such as training, the application becomes unusable. To avoid this we work
with *Jobs*, a procedure or function that runs when possible, and a *JobQueue*, to keep track of pending jobs and run them.

At the moment there are two different *Jobs*, the *ModelJob* which consists of training a model and the **ExplainerJob** in charge of
generating the explanation of a model. Both *Jobs* inherit from the abstract class *BaseJob*.

The *Jobs* are generated in the API when the client calls the **POST** */job* endpoint and then placed in the *JobQueue*. The request is answered
immediately leaving the API operational.

After the *Jobs* are queued, another asynchronous process retrieves and executes them in a parallel process.

To do this, the asynchronous process executes the following steps:

* Retrieves the data needed to execute the Job: Using the *get_args* method.
* Executes the *Job*: Using the *run* method. This method sends the results to the main process using a pipe.
* Store the results: Using the *store_results* method. This method stores all important data in the database.

Once the *Job* is executed and its results are stored, the asynchronous process retrieves the next *Job* in the queue, if no other *Job*
is pending, the process waits asynchronously until a *Job* is retrieved.

If an error occurs while executing a *Job*, it is added to the software log and the next *Job* (if any) is executed.
