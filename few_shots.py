few_shots = [
    {
      'Question' : "How many t-shirts do we have left for Nike in XS size and white color?",
      'SQLQuery' : "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Nike' AND color = 'White' AND size = 'XS'",
      'SQLResult': "Result of the SQL query",
      'Answer' : "25"
     },
    {
      'Question': "How much is the total inventory value for all small size t-shirts?",
      'SQLQuery':"SELECT SUM(price*stock_quantity) FROM t_shirts WHERE size = 'S'",
      'SQLResult': "Result of the SQL query",
      'Answer': "13429"
    },
    {
      'Question' : "If we have to sell all the Levi’s T-shirts today. How much revenue our store will generate without discount?" ,
      'SQLQuery': "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE brand = 'Levi'",
      'SQLResult': "Result of the SQL query",
      'Answer' : "12956" 
    },
    {
      'Question': "How many white color Levi's shirt I have?",
      'SQLQuery' : "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Levi' AND color = 'White'",
      'SQLResult': "Result of the SQL query",
      'Answer' : "43"
    }
]