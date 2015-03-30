# Lifestats

#### The problem
To retrieve N elements and calculate statistics may seem a trivial problem when N is relatively a small number. However at a large scale, this is not so trivial at all. 

In this scenario, we need to apply a distributed paradigm and split the space of items into different subsets. The given solution splits the space into 100 subsets and assigns each subset to a process which will iterate over the subset and extract partial statistics. Once a process finishes, it will send its data to the application.

##### Data structures
The calculation of the statistics is another problem which had to be addressed in a smart way. The data structure selection is critical in this case since iterating over and maintaining a large set of elements can be problematic. One of the most common approaches is to use a Hash Table since it allows data access in O(1) (in Python, the worst case will be O(n) but this is a extremely strange scenario and besides, we are dealing with numerical IDs). The problem this solution presents is that it is quite memory expensive. 

The data structure chosen was the [collections Counter](https://docs.python.org/2/library/collections.html#collections.Counter) which is a Python `dict` subclass and allows to retrieve the k ``most_common`` elements in O(k) + O((n - k) log k) + O(k log k) (See: http://stackoverflow.com/a/29240949).

##### Memory 
Given a 64 bits machine, Python 2.7.9 represents an integer with 24 bytes, this means that in the worst scenario (frequency one for every item, ``N = 150 million``):
```
(N * 24 Bytes) / 100 worker = 36.000.000 Bytes/worker = 34,3322753906 MB/worker
```

Obviously this solution is not optimal and could be improved. This would be work left for further iterations in the release cicle since the purpose of the project is to develop a working prototype. However it is worthy mentioning the possible improvements: 

###### Option 1: Send statistics every k-th page
By sending often the statistics to an aggregator process the processes would release memory and remain lighter.

```
k page/worker * 100 items/page = k * 10^2 item/worker
10^2*k item/worker * 24 Bytes/item = 2400 k  Bytes/worker
```

In this scenario the benefits of the solution might not be clear, but in case the frequencies of the elements vary (which happens to be the case), the aggregator process would also remove the duplicate entries, giving us a much better performance memory-wise at a high rate of duplicates. 

###### Option 2: Use of shared memory

This would be the best option memory wise since it does not involve maintaining one buffer per process. The main process would allocate two instances of ``SynchronousCounter`` in a common memory area shared with all the worker processes. Such data structure would contain all the data fetched by the processes and would allow to perform more advanced techniques such as **spawning** or **killing workers**, the application would start listening to the API and would perform operations based upon its load. 

At a cost of a greater programmational effort, the benefits would be remarkable.

##### Statistics
The script takes about 2 hours to complete its task at a rate of 100 requests per second when using 32 worker processes. Better rate limiting strategies may improve this.

##### Installation and requirements
* (developed) Python 2.7.9
* Install dependencies from ``requirements.txt``

##### Configuration
A ``config.yml`` file is provided, edit it so it suits your needs. 
It is possible to define different running environments depending on the needs, by default there are three defined: **development**, **test** and **production**.

###### Development (default)
A development server written in Ruby is provided for testing purposes. In distros such us **OS X** or **Ubuntu** a Ruby interpreter is already provided so just install the dependencies:
```sh 
$ gem install sinatra
```
and start the mock server:
```sh
ruby mocks/api.rb
```
Once the server is running: 
```sh
python main.py
```

###### Test
This project uses [Nose](https://nose.readthedocs.org/en/latest/).
```sh 
ENV=test nosetests
```

###### Production 
```sh
ENV=production python main.py
```


#### Author and copyright

Licensed under the [MIT License](http://en.wikipedia.org/wiki/MIT_License)

Luis Carlos Mateos Cañas. 2015
