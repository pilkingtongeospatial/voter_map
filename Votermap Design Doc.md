Even if you are building with Claude, the best results start with a hand written design document.

## Background

It is more important than ever to make sure that the electorate has easy access to information on voting. Sources such as Ballotopedia provide plenty of useful information, but lack an intuitive interface for organizing the information. The relevant information is organized on a left sidebar, with headings such as 2026 elections, 2025 elections, etc. This setup is useful, but a user has to go through several clicks to find state level information.

Maps provide an intuitive method for accessing information online. An efficient voter information page might involve a user clicking on their home state, and then receiving a pop up to relevant voting information, including but not limited to:

- Links to information on  how to register to vote in their state.
- Current ballot initiatives for the upcoming election cycle
- Contact information for representatives

The MVP for this map will involve an online  GIS map to be hostable and shareable on github. Future versions will involve online hosting for easy sharing.

## Structure
The landing page is described as follows:


A map of the  48 continental US states, with inset maps of Alaska and Hawaii. The state boundaries will be stored as geojsons obtained from US TIGER zip files. The states will be colored red or blue depending on how the state voted in the 2024 Presidential Election.

State abbreviations will need to have white masks so that they are easily visible against the background.

When the user clicks on a state the view zooms to a view of that state with Federal Congressional District boundaries, also hosted as geojsons.  A  window appears with links to  all relevant information. This will all be hosted in one folder, so that the information can be added to and updated easily over election. When a user clicks on a Congressional boundary, another browser window opens with information limited to that Congressperson.


The information will include:

- A link to the state’s page with information on how to register to vote.
- Links to contact information for every federal level Senator and Representative, accessible by a link of the Congressperson’s name and party.
Links to information on anyone running in the 2026 midterms, if it is available.
- This map needs to be in a state where it can be easily updated to be hosted online and shared for high frequency use. Search the web for the following:
State and Congressional district boundaries.
- A link to a page with voter registration information for each state.
- A homepage for every federal member of Congress, Senators and Representatives.


Write any needed data prep scripts, run them, and generate the local MVP map viewable in a browser. All of this needs to be in the current folder.

