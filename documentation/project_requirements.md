Objective: Create a billing system for Shopping Mall

Technology: Use Python (OOPs concept) for backend and Tkinter for frontend
Note: The user is the shopkeeper/biller using the application.


Requirements for each section:

Name of the application: OpenCart - Python billing system

INVENTORY
1. The Application should have the option to add, update, remove items from its inventory. 
2. Details should include an auto generated ID in the format "ITEM-(10 digit code)" - which will be uneditable, name of the item, category of the item, price, date added to inventory, date of manufacture and date of expiry.
3. The application should allow the user to add categories to items like vegetables, fruits, meat, dairy, eggs, cooking utensils, cleaning, stationery etc.
4. While adding an item if the category is not created, the user cannot add the item, for that we need to provide an option to create a category and add the item.
5. While adding the items, the user has to select from the list of available categories. The user can dynamically search for that category and add it.
6. In the all item view mode, the application should show all the item details stored in its inventory in proper row column formatting. 
7. In the all item view mode, there should be an option to sort the items based upon category, pricing, date added to inventory, date of manufacture and date of expiry.

CART
1. The application should allow the user to create one or multiple carts.
2. Each cart created will have an auto-generated unique invoice id, starting with "INVO-(10 digit code)"
3. The cart interface will contain the invoice id, date and time of the invoice, the fields to enter the details of the customer like name, phone number, apart from that it will have a section below where four columns for each item - Item Id, Item Name, quantity and price will be shown.
4. While billing the user can search via item id or item name, if item is present it should dynamically show in the UI with the total quantity availible and the user is supposed to click on the item. The quantity will be selected as 1 by default. If the user surpass the quantity than what is present in the inventory then he can't confirm the product and add to cart.
5. The application should allow the user to add, update (in terms of quantity) and remove items from each cart.
6. The application should allow the user to view the cart. 
7. When a user add, removes or updates the cart - The cart should immediately reflect the change.
8. The cart will show the total price - discount (if any) and should show the grand price
9. At the end the user should be able to generate the bill - a pdf file should be generated with invoice_id_date_time in the file name
10. The user should be able to add the discount %, the discount field should be set to 0 by default.
11. While billing the application should be able to take the buyer details like name, phone number which are mandatory alongside optional details like address
12. When filling the user details, the application should be able to dynamically search and suggest user details based upon their phone number only.

OPERATIONS
1. Use csv file handling to achieve this instead of SQL - peform CRUD operations on csv files.
2. Create multiple csv files as required for inventory handling and transaction handling
3. Any operation that the user will be performing will be logged to a logger file.
4. The application has to be a full screen desktop application.
5. Any kind of notification has to show in the bottom right corner.
6. For any item added, updated, removed from the inventory the notification should be updated.
7. For any item added, updated, removed from the cart the notification should be updated.
8. When the bill is generated the notification should pop.
9. Create proper folder structure to store the source code, the csv file database, the log folder for log files generated each day and a pdf folder for all the bills generated.
10. The pdf file bill should contain the name of the application/software that we are building.