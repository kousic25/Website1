// ---------------- AUTH SYSTEM ----------------


let loginMode = true;



const authButton =
document.getElementById("auth-submit-btn");


const authToggle =
document.getElementById("auth-toggle-action");



if(authButton){


authButton.addEventListener(
"click",
async function(){


let username =
document.getElementById(
"auth-username"
).value;



let password =
document.getElementById(
"auth-password"
).value;



let endpoint =
loginMode
?
"/api/login"
:
"/api/register";



let response =
await fetch(
endpoint,
{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify(
{
username,
password
}
)

}

);



let data =
await response.json();



if(data.success){

location.reload();

}

else{

document.getElementById(
"auth-error-msg"
).innerText =
data.message;

}


});


}





if(authToggle){


authToggle.onclick =
function(){


loginMode =
!loginMode;



document.getElementById(
"auth-title"
).innerText =
loginMode
?
"Sign In"
:
"Register";



document.getElementById(
"auth-submit-btn"
).innerText =
loginMode
?
"Sign In"
:
"Register";



document.getElementById(
"auth-switch-text"
).innerText =
loginMode
?
"Don't have account?"
:
"Already have account?";


authToggle.innerText =
loginMode
?
"Register here"
:
"Login here";


}


}





// ---------------- LOAD MEDIA ----------------


async function loadGallery(){


try{


let response =
await fetch(
"/api/media"
);



let media =
await response.json();



let container =
document.getElementById(
"folders-container"
);



if(!container)
return;



container.innerHTML="";



if(media.length===0){


container.innerHTML =
`
<h2>No Media Uploaded</h2>
`;

return;


}



media.forEach(
item=>{


let card =
document.createElement(
"div"
);



card.className =
"media-card";



if(item.type==="image"){


card.innerHTML =
`
<img src="${item.url}"
width="200">

<p>${item.folder_id}</p>

<button onclick="deleteAsset('${item.public_id}','image')">
Delete
</button>

`;



}

else{


card.innerHTML =
`
<video width="200" controls>

<source src="${item.url}">

</video>


<p>${item.folder_id}</p>


<button onclick="deleteAsset('${item.public_id}','video')">
Delete
</button>

`;

}


container.appendChild(card);


});


}

catch(error){

console.log(error);

}


}





// ---------------- UPLOAD ----------------


let uploadInput =
document.getElementById(
"media-files-input"
);



let uploadButton =
document.getElementById(
"btn-submit-gallery"
);




if(uploadButton){


uploadButton.onclick =
async function(){



let files =
uploadInput.files;



let folder =
document.getElementById(
"folder-name-input"
).value;



for(let file of files){



let formData =
new FormData();



formData.append(
"file",
file
);



formData.append(
"tag",
folder
);



await fetch(
"/api/upload",
{

method:"POST",

body:formData

}

);


}



loadGallery();



}


}





// ---------------- DELETE ----------------


async function deleteAsset(
public_id,
resource_type
){



await fetch(
"/api/delete-asset",
{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify(
{
public_id,
resource_type
}
)

}

);



loadGallery();


}





// initial loading

window.onload =
function(){


if(
document.getElementById(
"folders-container"
)
){

loadGallery();

}


};
