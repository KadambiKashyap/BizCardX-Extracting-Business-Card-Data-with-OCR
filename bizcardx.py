import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import numpy as np
import re
from PIL import Image
import mysql.connector as sql
import pandas as pd



my_db = sql.connect( 
             host="127.0.0.1",
             user="root",
             database = "BizcardX",
             port = 3306,
             password="2369",
              ) 
      
mycursor = my_db.cursor() 


#################################### FILE PATH ########################################

def file_input(path) : 
    im = Image.open(path)
    im_arr= np.array(im)
    reader = easyocr.Reader(['en'],gpu = False)
    text = reader.readtext(im_arr,detail= 0)
    return text, im


#################################### EXTRACTING DATA ###################################

def extract_data(data):
    result = {"NAME": [], "DESIGNATION": [], "ADDRESS": [], "COMPANY_NAME": [], "CONTACT": [], "EMAIL": [], "WEBSITE": [], "PINCODE": []}


    result["NAME"].append(data[0])
    result["DESIGNATION"].append(data[1])

    for item in range(2, len(data)):

        if "@"  in data[item] and ".com" in data[item]:
            result["EMAIL"].append(data[item].lower())

        elif 'www' in data[item] or 'WWW' in data[item] or 'wwW' in data[item]  and ".com" in data[item]:
            result["WEBSITE"].append(data[item].lower())

        elif "Tamil Nadu" in data[item] or "TamilNadu" in data[item]  or re.match(r'\b\d{6}\b', data[item])  or data[item].isdigit():
            result["PINCODE"].append(data[item])

        elif re.match(r"^[a-zA-Z\s,]", data[item]):
            result["COMPANY_NAME"].append(data[item])

        elif data[item].startswith("+") or (data[item].replace("-", "").isdigit()):
            result["CONTACT"].append(data[item])
            
        else:
            filtered_add = re.sub(r"[,;]", "", data[item])
            result["ADDRESS"].append(filtered_add)

    for key, value in result.items():
        if len(value)>0:
            something = ''.join(value)
            result[key] = [something]

        else:
            value = 'None'
            result[key] = [value]


            
    return result


    
#################################### SQL COVERSION ###################################

def convert_sql(x):
    table = ''' CREATE TABLE IF NOT EXISTS Card_details ( Name VARCHAR(225) PRIMARY KEY,
                                                          Designation VARCHAR(225),
                                                          Address VARCHAR(225),
                                                          Company_Name VARCHAR(225),
                                                          Contact VARCHAR(225),
                                                          Email VARCHAR(225),
                                                          Website VARCHAR(225),
                                                          Pincode VARCHAR(225) )'''
    mycursor.execute(table)
    my_db.commit()

    df = pd.DataFrame(x)

    insert_data = ''' INSERT INTO Card_details ( Name , Designation, Address, Company_Name, Contact, Email, Website, Pincode)
                                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
    

    for index, row in df.iterrows():
        values = tuple(row)
        mycursor.execute(insert_data, values)
        my_db.commit()

    return df


#################################### DELETE TABLE ###################################

def delete_table(x):
    mycursor.execute("DELETE FROM Card_details WHERE Name = %s ", (x,))
    table = mycursor.fetchall()
    my_db.commit()

    mycursor.execute("SELECT * FROM Card_details")
    table1 = mycursor.fetchall()

    df = pd.DataFrame(table1, columns = mycursor.column_names)

    my_db.commit()

    return df


    
#################################### STREAMLIT PAGE ###################################


st.title('**BizCardX: Extracting Business Card Data with OCR**', anchor = False)

selected = option_menu(
    menu_title = None,
    options=["Home", "Data Extraction & Modification"],
    icons=["house-fill","database-fill"],
    default_index = 0,
    menu_icon="cast",
    orientation="horizontal",
    key="navigation_menu",
    styles={
            "font_color": "#DC143C",   
            "border": "2px solid #DC143C", 
            "padding": "10px 25px"   
        }

)

if selected == 'Home':
  col1, col2 = st.columns(2)

  with col1:
   st.header(":red[Abstract] 	:bookmark_tabs:", anchor = False)
   st.divider()
   with st.container(height=500):
     st.markdown("#### EasyOCR is a python module for extracting text from image. It is a general OCR that can read both natural scene text and dense text in document.")

     st.markdown("#### The main purpose of BizcardX  is to automate the process of extracting essential details from Business Card images, which has relevant data. BizcardX is able to extract text from the images using EasyOCR.")

  with col2:
   st.header(":red[Tools] :wrench: ", anchor = False)
   st.divider()
   with st.container(height=500):
     st.markdown("- #### OCR \n - #### Streamlit \n - #### GUI \n - #### Python\n - #### MySQL Workbench\n - #### Data Extraction ")

if selected == 'Data Extraction & Modification' :
    file_type = st.file_uploader("Upload Image file", ["jpg", "jpeg", "png"])
    st.divider()

    if file_type is not None:
        st.image(file_type, width = 600)

        text, im = file_input(file_type)
        details = extract_data(text)
        if details:
            st.success("File Extracted Successfully")
        df = pd.DataFrame(details)

        st.dataframe(df, use_container_width=True)

        click = st.button("Store into SQL Databses", use_container_width = True)

        if click:
            sql_table = convert_sql(details)

            st.success("Upload Sucessful to MySQL")
        
        st.divider()

        #Preview the table
        query = "SELECT * FROM Card_details"

        mycursor.execute(query)
        table = mycursor.fetchall()
        my_db.commit()

        df1 = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "ADDRESS", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "PINCODE"))
        # Modify the Table:
        st.subheader("MODIFY TABLE :")
        st.divider()
        selected = st.selectbox("Select Name to Modify", df1["NAME"])
        df_modify = df1[df1["NAME"]== selected]
        df_changed = df_modify.copy()

        new_name = st.text_input("Name", df_modify["NAME"].unique()[0])
        new_designation = st.text_input("Designation", df_modify["DESIGNATION"].unique()[0])
        new_add = st.text_input("Address", df_modify["ADDRESS"].unique()[0])
        new_company_name = st.text_input("Company_name", df_modify["COMPANY_NAME"].unique()[0])
        new_contact = st.text_input("Contact", df_modify["CONTACT"].unique()[0])
        new_email = st.text_input("Email", df_modify["EMAIL"].unique()[0])
        new_website = st.text_input("Website", df_modify["WEBSITE"].unique()[0])
        
        new_pincode  =st.text_input("Pincode", df_modify["PINCODE"].unique()[0])

        df_changed["NAME"] = new_name
        df_changed["DESIGNATION"] = new_designation
        df_changed["ADDRESS"] = new_add     
        df_changed["COMPANY_NAME"] = new_company_name
        df_changed["CONTACT"] = new_contact
        df_changed["EMAIL"] = new_website
        df_changed["WEBSITE"] = new_email 
        df_changed["PINCODE"] = new_pincode

        button = st.button("Modify Table", use_container_width = True)
    
        if button:
            mycursor.execute(f"DELETE FROM Card_details WHERE NAME = '{selected}'")
            my_db.commit()

            # Insert Query

            insert_query = '''INSERT INTO Card_details(Name, Designation, Address, Company_name, Contact, Email, Website, Pincode)
                                                   values(%s,%s,%s,%s,%s,%s,%s,%s)'''

            new_data = df_changed.values.tolist()[0]
            mycursor.execute(insert_query,new_data)
            my_db.commit()

            st.success("SUCCESSFULLY MODIFIED THE TABLE")
            st.dataframe(df_changed)
        
        st.divider()

        st.subheader("You wish to delete a record in SQL Table? Click Below 👇")

        query2 = "SELECT Name FROM Card_details"

        mycursor.execute(query2)
        table = mycursor.fetchall()
        my_db.commit()

        total_names=[]
        for i in table:
            total_names.append(i[0])
        
        all_names = st.selectbox("Select Name to Delete", total_names)

        click2 = st.button("Delete Record", use_container_width = True)
        if click2:
            mycursor.execute(f"DELETE FROM Card_details WHERE name = '{all_names}' ")
            my_db.commit()
            
            st.warning("ERASED SUCCESFULLY")
            mycursor.execute("SELECT * FROM Card_details")
            tab = mycursor.fetchall()
            my_db.commit()
            df_deleted = pd.DataFrame(tab, columns=("NAME", "DESIGNATION", "ADDRESS", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "PINCODE"))

            st.dataframe(df_deleted)







        

