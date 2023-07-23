# Food Delivery Service Company

A food delivery service company is an organization that specializes in delivering food from restaurants, cafes, or other food establishments to customers' doorsteps. These companies act as intermediaries between the customers and the food providers, facilitating the ordering and delivery process.

## Workflow
The typical workflow of a food delivery service company involves the following steps:

1. Online Platform: The company operates an online platform, such as a website or mobile app, where customers can browse through a variety of restaurants, menus, and food options available for delivery in their area.

2. Ordering: Customers select the items they want to order and add them to their virtual cart. They can customize their orders based on their preferences, dietary requirements, and any special instructions.

3. Payment: Once the order is finalized, customers proceed to the payment stage, where they make online payments using various methods like credit/debit cards, digital wallets, or other payment options supported by the platform.

4. Restaurant Notification: The food delivery service company notifies the respective restaurant or food establishment about the order, either through an automated system or via dedicated restaurant portals integrated with the platform.

5. Food Preparation: The restaurant starts preparing the order, just as they would for a dine-in customer.

6. Delivery Assignment: The food delivery service company assigns a delivery driver or courier to pick up the order from the restaurant and deliver it to the customer's specified address.

7. Delivery: The delivery driver picks up the food and delivers it to the customer's location within the estimated time frame.

8. Customer Support: Food delivery service companies usually have customer support available to address any issues or inquiries related to the order, such as tracking the delivery or resolving any problems with the food.

### Workflow - Area Definition
For customers, The geometric region is splitted into __areas__, But for the runners who delivery the order, it is splitted into __pools__ where pool could include multiple areas together.

### Workflow - EDT
EDT is stands for Estimated Delivery Time, which is the time estimated for an order to be delivered. Depending on the company business strategy to determine the EDT and where to let the customer see it, most of the company has two EDTs, one for a pre-order state, and the other for the post-order state.

The Pre-orders state is when the customer didn't place an order yet, and just exploring and discovering the available restaurants according the location of the customer. In this stage, we don't have exact location of the customer, but only the area where the searching is made at the current time, that's why we don't have an accurate EDT estimation is this stage.
Also, all other available time feature like runners occupancy will be on average. 

The Post-order state is when the order is already placed, so the available information of exact user location and exact order placing time are defined, which will help to have more accurate EDT estimation.

During Calculating the EDT in post-order state, there are two methods for that calculation, either calculating the EDT as a whole value, or estimating each step in the EDT and summing them together to get the total EDT value.

EDT could be splitted into multiple stages, which differ from company to another:
1. First Mile 'FM': The time taken by the runner who deliver the order from __Acceptting the order__ till __Arriving to the restaurant__.
2. Cooking Time 'CT': The time taken by the restaurant preparing the food, which is defined from __restaurant accept the order__ till __The food is ready__.
   - But some the company don't have an indicator from the restaurant to know if they have finished preparing the food, So in this case the CT is calculated from __Runner Arrived to restaurant__ till __Runner Is Out For Delivery__.  

## Target KPIs
Key Performance Indicators (KPIs) are important metrics that food delivery service companies use to measure the success and efficiency of their operations. These KPIs help monitor various aspects of the business and guide decision-making. Here are some essential KPIs that such companies often target:

|KPI|Description|
|---|---|
|Runner Occupancy|The total number of available free runners who are not assinged to any orders over the total number of runners in the region.<br/>This gives indication of how free runners available in current time, and help to monitor each region of oversupply and undersupply, and control the region disabling process where a region is disabled so the customers can't place an orders at the current time in that region, as there are no free runners availalbe to deliver.|
|Runners UTR 'Utilization Rate'|This KPI estimate the rate of number of orders being deliverd by the runner.|
|Order Volume| The total number of orders processed within a specific time frame (daily, weekly, or monthly). <br/>Increasing order volume indicates growing demand for the service.
|Customer Retention Rate| The percentage of customers who return to use the service again after their initial order. <br/>A high customer retention rate indicates customer satisfaction and loyalty.
|Average Order Value (AOV)| The average amount spent by customers on each order. <br/>Increasing the AOV can boost revenue and profitability.
|Delivery Time| The average time taken to deliver an order from the time it was placed. <br/>Reducing delivery time enhances customer satisfaction and improves the overall user experience.
|On-Time Delivery Rate| The percentage of orders delivered within the estimated delivery time. <br/>A high on-time delivery rate is crucial for customer satisfaction.
|Customer Satisfaction (CSAT) Score| Measuring customer satisfaction through surveys or ratings to gauge the quality of service provided.
|Restaurant Partner Satisfaction| Assessing the satisfaction levels of partner restaurants to ensure strong relationships and quality of service.
|Order Accuracy| The percentage of orders that are delivered without mistakes or missing items. <br/>High order accuracy is vital for customer satisfaction.
|Delivery Cost per Order| Calculating the average cost incurred per order for delivery. <br/>Reducing delivery costs can improve profit margins.
|Customer Acquisition Cost (CAC)| The cost associated with acquiring a new customer. <br/>Reducing CAC ensures efficient use of marketing budgets.
|Return Rate| The percentage of orders that are returned or refunded due to issues with the order. <br/>A low return rate signifies better quality control.
|Average Delivery Distance| The average distance traveled for each delivery. <br/>Optimizing delivery routes can reduce costs and increase efficiency.
|Driver Performance Metrics| Metrics like on-time delivery, delivery completion rate, and customer ratings for drivers. <br/>Ensuring driver efficiency and satisfaction is crucial for smooth operations.
|Market Share| Measuring the company's share of the food delivery market compared to competitors.
|Revenue and Profitability| Monitoring overall revenue and profitability to assess the company's financial health.


## Target KPIs Calculation
|KPI|Calculation|
|---|---|
|Order Volume|Count the total number of orders processed within the specified time frame (e.g., daily, weekly, or monthly).
|Customer Retention Rate|Determine the number of customers who returned to use the service again within a specific period. <br/>Divide this number by the total number of unique customers during that time and multiply by 100 to get the retention rate.<br/>Customer Retention Rate = (Number of Returning Customers / Total Number of Unique Customers) * 100
|Average Order Value (AOV)|Add up the total revenue generated from all orders within a specific period and divide it by the total number of orders.<br/>AOV = Total Revenue / Total Number of Orders
|Delivery Time|Calculate the time taken for each order from the moment it was placed to when it was delivered. <br/>Then, find the average delivery time across all orders within a specific time frame.
|On-Time Delivery Rate|Determine the number of orders delivered within the estimated delivery time. <br/>Divide this by the total number of orders and multiply by 100 to get the on-time delivery rate.<br/>On-Time Delivery Rate = (Number of On-Time Deliveries / Total Number of Orders) * 100
|Customer Satisfaction (CSAT) Score|Conduct customer surveys or use rating systems to collect customer feedback. <br/>Calculate the average rating or satisfaction score across all responses.
|Restaurant Partner Satisfaction|Conduct surveys or collect feedback from partner restaurants to measure their satisfaction. <br/>Calculate the average satisfaction score or percentage of satisfied partners.
|Order Accuracy| Determine the number of orders delivered without mistakes or missing items. <br/>Divide this by the total number of orders and multiply by 100 to get the order accuracy rate.<br/>Order Accuracy = (Number of Accurate Orders / Total Number of Orders) * 100
|Delivery Cost per Order| Calculate the total delivery costs (including labor, fuel, etc.) and divide by the total number of orders.<br/>Delivery Cost per Order = Total Delivery Costs / Total Number of Orders
|Customer Acquisition Cost (CAC)|Add up all marketing and sales expenses incurred within a specific time frame to acquire new customers. <br/>Divide this by the number of new customers acquired in that period.<br/>CAC = Total Marketing and Sales Expenses / Number of New Customers Acquired.

## Main Projects
|Project|Descriptio|
|--|--|
|Demand Forecasting| Develop a demand forecasting model to predict the number of orders and their types (e.g., cuisine, meal time) for specific days or time slots. <br/>This can help food delivery companies allocate resources effectively, optimize inventory management, and ensure timely deliveries during peak hours.<br/>The estimated orders demands could be on hourly basis for long interval of time like a whole week.|
|EDT "Estimated Delivery Time" Estimation|Develop a model to estimate the EDT for order delivery based on certain features and depending on each pool/area the company delivery to. <br/>There are two possible stages for EDT values to consider, the Pre-order state when the order is not placed yet by the customer, and Post-order state when the order is actually placed.<br/>The EDT has multiple stages which toghether they define the EDT value and differ from company to another|
|Runners Shift Plannig Automation|Automate the process of runners shifts planning according to their estimated forecasted orders demands, time slots and shifts long|

## Related Projects
|Project|Description|
|--|--|
|Recommender System| Build a personalized recommender system that suggests restaurants and food items based on a customer's previous orders, preferences, and user behavior. <br/>This can enhance customer engagement, increase average order values, and improve customer retention.|
|Customer Churn Prediction| Create a model to predict which customers are at risk of churning (stopping using the service) based on their ordering patterns, frequency, and satisfaction scores. <br/>By identifying potential churners, the company can implement targeted retention strategies.|
|Route Optimization| Utilize data science techniques to optimize delivery routes and minimize delivery time and costs. <br/>Consider factors such as traffic conditions, order locations, and real-time updates to improve the efficiency of the delivery fleet.|
|Sentiment Analysis| Perform sentiment analysis on customer reviews and feedback to gain insights into customer satisfaction and pain points. <br/>This information can be used to identify areas for improvement and enhance the overall customer experience.|
|Customer Segmentation| Use clustering algorithms to segment customers based on their ordering behavior, demographics, and preferences. <br/>This can help tailor marketing strategies and promotions to different customer groups effectively.|
|Fraud Detection| Develop a fraud detection system to identify and prevent fraudulent activities, such as fake orders or payment fraud. <br/>This can safeguard the company's reputation and financial interests.|
|Dynamic Pricing| Implement dynamic pricing algorithms that adjust food prices based on various factors like demand, time of day, and inventory levels. <br/>Dynamic pricing can maximize revenue and encourage customers to order during off-peak hours.|
|Inventory Management| Use predictive analytics to optimize inventory management by forecasting demand for various food items. <br/>This ensures that the right amount of ingredients and supplies are stocked, reducing wastage and cost.|
|A/B Testing for Marketing Campaigns| Conduct A/B testing on marketing campaigns to measure the effectiveness of different promotions, discounts, or incentives. <br/>This allows the company to fine-tune marketing strategies and identify the most impactful campaigns|
