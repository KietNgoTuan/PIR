# PIR Project
[PIR] Innovative Architecture using XOR operation to optimize network occupation 

Project done by 5 telecommunication students of the french engineering 
school INSA Lyon. 

[HOW TO USE IT]

Execute it using python 3 or later version 

    python client.py && python server.py
    
    Check your version using the following command : python --version
    

   If you desire to change the maximum of files that can be stored in the
   tempopary memory, modifiy the value of the if statement condition (line 371)
   
   Initialy a _TCP connection_ will be initialized between the client and the server (that will be initially launched).
   This first connection will allow the client to make a file request by typing 
   the **exact name of the required file**. The server will wait until the required amount of request referred in
   the server code is reached. 
   
   Straight after the first flag will be send through a _UDP Broadcast_ `[SENDINGS]$<amount of successive sendings>`
   Thanks to this information each client when to listen and especially when to stop listening.
   
   In order to inform all clients of the operation done by the decision matrix, a new flag will be send using the same connexion as before
   . This new flag goes as follow `[FLAGS]$[(hash of file involved in XOR, size of this file, popularity of this file)]` 
   
   If this flag concerns a unique file then the client won't have to decode it by repeating the XOR operation. Otherwise this operation will be executed on the received file
  .
  
  After those flags the file will be send  on the whole sub-network using the broadcast IP address.
  
  In order to decrease the server charge in this excessively centralized architecture, a **Peer to Peer** mechanism has been implemented. Thus if a client is the only one asking for a certain file and no XOR operation is relevant on this file, then if another client owns this file, each concerned client will launch a **thread** in order to asynchronously generate a TCP P2P connection `[FLAG_D2D]$ip_host->ip_dest`
  between both. That way the server charge will significantly deacrese and the QoS will slightly increase.    
  
  Furthermore on order to drastically optimize the QoS, this algorithm implements a **multiprocessing encoding system**
  by taking advantage of the multi-core CPU architecture. A possible upcoming feature might use the GPU in order to keep on minimizing the time of reception.
  
  So far the decision matrix will pick the combination with the lowest amount of succesive sendings. Basically it will know the different file requests and the different files stored by each user 
  
  [REQUIRED PACKAGE]
  
  The server will work with a **MYSQL database api** that we'll get connected to using 
  the mysql-connector package so please install this package thanks to the following instruction 
  
  `if you have pip as an environement variable  : pip install mysql-connector`
  
   `if not : python -m pip install mysql-connector`
   
   Install mysql and create a schema named **PIR** and a database
   named **videos** as it follows : 
   ![database structure](C://Images/sql_database.png)
   After that, lauch the database server and modify the different information in the server code regarding the connection parameter if required (if you get a message saying : cannot reach database then modify the parameters line 448)
   
   Moreover in order to get realistic popularity coefficient we directly use the Youtube Data APIv3
   . If you want to re-use this service (we recommend it) please get a new private API key thanks to this link : https://developers.google.com/youtube/v3/ .
   In the server code copy this new key line 427 : 
   `PRIVATE_YOUTUBE_KEY = <your private API key>` 
   
   If you add a new video then add its youtube id (pick it in the URL)
   and put in the dict() named YOUTUBE_DICT (line 430)
   
   If you need more information or want to improve our architecture please contact me personnaly on my student address : 
   **matthieu.raux@insa-lyon.fr**
   
   Sincere thanks to my colleagues : 
   Adrea RICO, Allan GOUDJI, Beatriz DE CARVALHO, Kiet THEO
   
   And a sincere thanks to the two searchers we worked with for their precious advices and their time:
   Leonardo CARDOSO & Jean Marie GORCE 
   
   



