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
      //   logout() {
      //     //alert("No magic on the server yet. You'll have to write the logout code there.");
      //     axios
      //     .delete(this.serviceURL+"/logout")
      //     .then(response => {
      //         this.currentUserId = null;
      //         location.reload();
      //     })
      //     .catch(e => {
      //       console.log(e);
      //     });
      //   },

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
        // `this` points to the vm instance
        
        return this.tasks.filter(task => task.status == "pending")
      },

      getFailedTasks: function () {
        // `this` points to the vm instance
        
        return this.tasks.filter(task => task.status == "failed")
      },

    },
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
    