# UOCIS322 - Project 6 #

## Author: Raul Patel

## Contact: raulp@uoregon.edu

## Description

Brevet time calculator.

Reimplement the RUSA ACP controle time calculator with Flask and AJAX.

For the initial project, we took the algorithm of the ACP controle time calculator 
and implemented it in AJAX for a single page dynamic site. We also 
implemented Nose testing for the logic to account for any error cases.
Then we added mongodb in the backend to hold the values we loaded into the table.
Then, we added a basic api with a simple website interface so
that we can query the database for relevant information and display it. Our website communicates
with the API through GET requests to receive the information to display.
Now, finally, we have implemented a way for users to create accounts get authorization to access restricted resources
through flask-login and WTForms. We store the user info in a database so that we can verify users later.

The algorithm uses minimum and maximum speeds for sections of a brevet to calculate the open and closing
times for each checkpoint. We do this by simply dividing the distance by the minimum speed for the 
closing and the maximum speed for the opening.
