console.log("Fliq.js Loaded");


const trackSubmissionCount = (function(){ 
  let count= 0;
  return function (){
    count ++;
    return count;
  }
})();


const validateBlogForm = () => {
    const title = document.getElementById("blog-title").value.trim();
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const content = document.getElementById("content").value.trim();
    const category = document.getElementById("category").value;
    const termsChecked = document.getElementById("terms").checked;
  
    if (!title || !name || !email || !content || !category) {
      alert("All fields are required!");
      return false;
    }
  
    if (content.length <= 25) {
      alert("Blog content should be more than 25 characters");
      return false;
    }
  
    if (!termsChecked) {
      alert("You must agree to the terms and conditions");
      return false;
    }
  
    return true;
  };
  function handleFormSubmit(event) {
    event.preventDefault();
    
    if (!validateBlogForm()) {
        return false;
    }

    const title = document.getElementById("blog-title").value.trim();
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const content = document.getElementById("content").value.trim();
    const category = document.getElementById("category").value;
    
    const blogSubmission = {
        title: title,
        name: name,
        email: email,
        content: content,
        category: category,
        timestamp: new Date().toLocaleString()
    };

    const jsonstring =JSON.stringify(blogSubmission);
    console.log("JSON string:", jsonstring);

    const parsedObj = JSON.parse(jsonstring);

    const{title: parsedTitle, email:parsedEmail } = parsedObj;
    console.log("Parsed Title:", parsedTitle);
    console.log("Parsed Email:", parsedEmail);

    const updatedParsedObj = {
      ...parsedObj,
      submissionsDate: new Date().toISOString(),
    };
    console.log("Updated Objects:",updatedParsedObj);

    const count=trackSubmissionCount();
    console.log(`Succesfull,${count}`);


    addSubmission(blogSubmission);
    
    document.getElementById("blog-title").value = "";
    document.getElementById("name").value = "";
    document.getElementById("email").value = "";
    document.getElementById("content").value = "";
    document.getElementById("category").value = "";
    document.getElementById("terms").checked = false;

    alert("Blog published successfully!");
    
    return false;
}

function addSubmission(blogData) {
    const submissionsList = document.getElementById('submissions');
    
    const listItem = document.createElement('li');
    listItem.style.marginBottom = '1rem';
    listItem.style.padding = '1rem';
    listItem.style.border = '1px solid #ddd';
    listItem.style.borderRadius = '5px';
    listItem.style.backgroundColor = '#f9f9f9';
    
    listItem.innerHTML = `
        <h3>${escapeHtml(blogData.title)}</h3>
        <p><strong>Author:</strong> ${escapeHtml(blogData.name)}</p>
        <p><strong>Email:</strong> ${escapeHtml(blogData.email)}</p>
        <p><strong>Category:</strong> ${escapeHtml(blogData.category)}</p>
        <p><strong>Content:</strong> ${escapeHtml(blogData.content)}</p>
        <p><small><strong>Published:</strong> ${blogData.timestamp}</small></p>
    `;
    
    submissionsList.insertBefore(listItem, submissionsList.firstChild);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
});