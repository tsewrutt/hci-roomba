Vue.component("modal", {
    template: "#modal-template"
  });
  
var app = new Vue({
    el: "#app",
  
    //------- data --------
    data: {
      serviceURL: `http://localhost:5000`,
      fetchuser: null, 
      view: null,
      loggedIn: null,
      checkUser: null,
      in: null,
      tasks:[],
      input: {
        username: "",
        password: ""
      }
    },
  
    methods: {
      login() {
        
        if (this.input.username !== "" && this.input.password !== "") {
            const userDocsinCollection = db.collection('users').get();
           // const docSnap = getDoc(docRef);
           //const usersDoc = db.getDocs(userCollection)
           userDocsinCollection.then((users) => {
            users.forEach((user) => { 
                console.log(user.id)
                //user.data gives me the json content, then if you want to ref a specific thing inside of it do . whatever var you want to fetch
                if(this.input.username == user.id && this.input.password == user.data().password){
                    //we move forward
                    this.loggedIn = user.id;
                    this.checkUser = true;
                    return;
                }
            })
            //Create new user
            if(this.checkUser == null){
                var newUserData = {
                    password: this.input.password
                }
                db.collection("users").doc(this.input.username).set(newUserData).then(() => {
                    this.loggedIn = this.input.username;
                    this.checkUser = true; //log them in right away after sign up
                    console.log("User Created, then update page");
                });
            }
            if(this.loggedIn == null){
                alert("Wrong Password! Try Again.");
            }
           })
           

            // if (docSnap.exists()) {
            // console.log("Document data:", docSnap.data());
            // } else {
            // // docSnap.data() will be undefined in this case
            // console.log("No such document!");
            // }
        
        } else {
          alert("Both username and password fields are required.");
        }
      },
  
      logout(){
        this.checkUser = false;
        this.loggedIn = null;
        this.view = null;
      },

      alltasks() {
        console.log("tasks requested");
        this.view = "tasks"
        // onSnapshot listens to real-time updates on the collection
        db.collection("tasks").onSnapshot((content) => {
          this.tasks = [];
          content.forEach((doc) => {
            this.tasks.push(doc.data()); // This puts all the doc in the tasks
          }); 
        }); 
      },

      // taskProgressSetter(time, expectedtime){
      //   this.currTime = time;
      //   this.timerequired = expectedtime;
      //   return getProgressPercentage();
      // }

    },

    computed: {
      // a computed getter
      getCompletedTasks: function () {
        // `this` points to the vm instance
        return this.tasks.filter(task => task.status == "completed")
      },

      getIncompleteTasks: function () {
        // `this` points to the vm instance
        return this.tasks.filter(task => task.status == "incomplete")
      },

      getPendingTasks: function () {

        return this.tasks.filter(task => task.status == "pending")
                .map(task => {
                //var currTime = new Date()
                // //var startTime = task.starttime.toDate()
                // //duration in seconds

                duration = (new Date() - task.starttime.toDate())/ 1000
                // //added a new attribute to task in the json dict called progress
                var newTask = task
                const clamp = (num, min, max) => Math.min(Math.max(num, min), max)

                newTask.progress = clamp((duration/task.timerequiredfortask) * 100,0,100)                
                
                return newTask

                });
        },

      getFailedTasks: function () {
        // `this` points to the vm instance
        
        return this.tasks.filter(task => task.status == "failed")
      },

      // taskProgressPercentage: function(task){
      //     return (task.timetaken / task.timerequiredfortask) * 100;
      // },

    },

    beforeDestroy() {
      // prevent memory leak
      clearInterval(this.interval)
    },
    created() {
      // update the time every second
      this.interval = setInterval(() => {
        this.tasks = this.tasks.map(task => { if(task.status == "pending"){
          duration = (new Date() - task.starttime.toDate())/ 1000
                // //added a new attribute to task in the json dict called progress
                var newTask = task
                const clamp = (num, min, max) => Math.min(Math.max(num, min), max)

                newTask.progress = clamp((duration/task.timerequiredfortask) * 100,0,100)                
                
                return newTask
        }else{
          return task
        }
      })
      }, 1000)
    }

  //------- END methods --------
  
});











      //WE would do this way if we didnt already import these in the html file through <script> tag
  // const { initializeApp } = require ('firebase/app');
  // const { collection, getFirestore } = require('firebase/firestore');
  // const { doc, getDoc } = require('firebase/firestore');

  // // TODO: Add SDKs for Firebase products that you want to use
  // // https://firebase.google.com/docs/web/setup#available-libraries

  // // Your web app's Firebase configuration
  // // For Firebase JS SDK v7.20.0 and later, measurementId is optional
  // const firebaseConfig = {
  //   apiKey: "AIzaSyDMl6mFALQU0b3KyOn6rAA3iT1vyi9r6EY",
  //   authDomain: "hri-roomba-data.firebaseapp.com",
  //   databaseURL: "https://hri-roomba-data-default-rtdb.firebaseio.com",
  //   projectId: "hri-roomba-data",
  //   storageBucket: "hri-roomba-data.appspot.com",
  //   messagingSenderId: "761382477216",
  //   appId: "1:761382477216:web:5f3497912c8add63a158c5",
  //   measurementId: "G-M5HZY6L9ER"
  // };

  // Initialize Firebase
  // fb_app = initializeApp(firebaseConfig);

  // Initialize Cloud Firestore and get a reference to the service
  ///const db = getFirestore(fb_app);
    