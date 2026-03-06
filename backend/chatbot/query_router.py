import sqlite3
import os
from pathlib import Path
from chatbot.gemini_client import ask_gemini, generate_sql_query, generate_natural_response

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "chat_data.db"

def get_db_schema():
    if not DB_PATH.exists():
        return "No database found."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema = "\n".join([row[0] for row in cursor.fetchall() if row[0]])
    conn.close()
    return schema

def clean_sql(sql_str):
    # Remove markdown blocks if Gemini included them
    sql_str = sql_str.strip()
    if sql_str.startswith("```sql"):
        sql_str = sql_str[6:]
    if sql_str.startswith("```"):
        sql_str = sql_str[3:]
    if sql_str.endswith("```"):
        sql_str = sql_str[:-3]
    return sql_str.strip()

def handle_query(query):
    worker_profile = query.get("worker_profile")
    question = query.get("question")
    
    try:
        schema = get_db_schema()
        if "No database found" in schema:
            return "Database missing. Please ask administrator to initialize."
        
        # 1. Ask Gemini to convert natural language to SQL
        raw_sql = generate_sql_query(question, schema)
        sql = clean_sql(raw_sql)
        
        # 2. Execute SQL against database
        conn = sqlite3.connect(DB_PATH)
        # Avoid execution of destructive operations purely for safety
        if "DROP" in sql.upper() or "DELETE" in sql.upper() or "UPDATE" in sql.upper() or "INSERT" in sql.upper():
             conn.close()
             return "Query blocked due to safety restrictions."

        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        
        # Get column names
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        conn.close()
        
        # Format results slightly
        formatted_results = "No records found matching the criteria."
        if results:
            sliced_results = list(results)
            if len(sliced_results) > 20:
                sliced_results = sliced_results[0:20]
            
            mapped = []
            for row in sliced_results:
                row_dict = {}
                for i, col in enumerate(column_names):
                    row_dict[col] = row[i]
                mapped.append(row_dict)
                
            data_str = str(mapped)
            formatted_data = data_str[0:3000]
            
            if len(results) > 20: 
                formatted_results = f"Found {len(results)} results (showing top 20):\n" + formatted_data
            else:
                formatted_results = formatted_data

        # 3. Ask Gemini to turn results into natural response
        final_answer = generate_natural_response(question, formatted_results, worker_profile)
        
        return final_answer
        
    except Exception as e:
        return f"Error processing query: {str(e)}\n\n(Generated SQL was: {raw_sql if 'raw_sql' in locals() else 'None'})"
