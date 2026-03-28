---
description: Movie Recommendation System
---

# Project Architecture
This is a React + Flask app, the frontend is built using React and Vite whilst the backend is build using Flask. The application runs entirely locally on the users device. The role of the app is to generate movie recommendations for users. A user can register an account or login. They have to supply movie they like during onboarding which is then saved to a sqlite database. The app will use this information to make predictions about what movies the user might enjoy.

# Project Structure
This is how the project is structured:
- All backend code in `/api`
- API endpoints are in `/api/app/main` and `/api/app/auth`
- For the frontend, components are in `src/components`
- Pages that are on the page are in `src/pages`

# Coding standards
For JavaScript, we write in everything like this:

```javascript
function helloWorld( )
{
    console.log( "Hello world!" );
}

function makeAPIRequest( data )
{
    axios.get( "/api/test" ).then( ( response ) =>
    {
        console.log( response.data );
    } )
    .then( ( response ) =>
    {
        console.log( response.data );
    });
}
```
These are just examples as to how code is layed out and formatted.