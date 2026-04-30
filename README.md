# Frontend Documentation

## Overview

The frontend is a web application that allows users to manage products, categories, and sales.

## Prerequisites

- Node.js installed
- npm installed

## Important Notes

- There are 3 user types: Owner, Admin, and Casher.
- The Owner can do everything.
- The Admin can do everything except delete the Owner.
- The Casher can only make sales and view products and clients.

## Main UX

### User Management Page

- There is a list of users, with their information, and you can edit or delete them.
- To delete a user, you must click on the trash can icon.
- To edit a user, you must click on the edit icon.
- The user information is displayed in a table with the following columns: Username, Email, First Name, Last Name, Phone Number, Address, Role.

### Chatbot Management Access

This page is only accessible to Owner and Admin users.

This page is used to manage the permission to use the chatbot implemented on telegram.

### Client Management Page

- There is a list of clients, with their information, and you can edit or delete them(delete it soft delete).
- To delete a client, you must click on the trash can icon.
- To edit a client, you must click on the edit icon.
- The client information is displayed in a table with the following columns: Name, Last Name, Email, Phone Number, Address.

### Product Management Page

- There is a list of products, with their information, and you can edit or delete them.
- To delete a product, you must click on the trash can icon.
- To edit a product, you must click on the edit icon.
- The product information is displayed in a table with the following columns: Name, Description, Price, Stock, Category.

### Provider Management Page

- There is a list of providers, with their information: name, email, phone number, and address, and you can edit or delete(soft delete) them.

### Metrics Pages ("Metricas" && "MetricasProducto")

- These pages are only accessible to Owner and Admin users.
- In "Metricas" you can see the best selling products and the best selling clients.
- In "MetricasProducto" you can see the best selling products in a chart.
- These metrics are calculated based on the sales made in the system that are sended by the API saved in the database.
- The sales are sended to the API using the endpoint "/api/sales".
- The metrics are updated every time the page is loaded.
