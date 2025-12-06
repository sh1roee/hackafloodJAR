"""
Test script to display price data from the December 5, 2025 Daily Price Index
"""

from pdf_parser import PricePDFParser
import pandas as pd

# Set display options for pandas
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

def main():
    print("="*80)
    print("DA DAILY PRICE INDEX - DECEMBER 5, 2025")
    print("National Capital Region (NCR)")
    print("="*80)
    
    parser = PricePDFParser()
    
    # Parse the PDF
    tables = parser.parse_latest_pdf(show_text=False)
    
    if not tables:
        print("No tables found!")
        return
    
    print(f"\nTotal tables extracted: {len(tables)}")
    
    # Filter out small tables (likely headers/footers)
    main_tables = [df for df in tables if df.shape[0] > 5]
    
    print(f"Main data tables: {len(main_tables)}\n")
    
    # Display each main table
    for i, df in enumerate(main_tables, 1):
        # Clean the dataframe
        df_clean = df.copy()
        
        # Remove None columns
        df_clean = df_clean.loc[:, df_clean.columns.notna()]
        
        # Rename columns to clean them up
        new_columns = []
        for col in df_clean.columns:
            if col and isinstance(col, str):
                # Clean up column names
                clean_col = col.replace('\n', ' ').strip()
                new_columns.append(clean_col)
            else:
                new_columns.append('Unknown')
        
        df_clean.columns = new_columns
        
        print("="*80)
        print(f"TABLE {i} - Page {df.attrs.get('page', '?')}")
        print("="*80)
        print(f"Shape: {df_clean.shape[0]} rows × {df_clean.shape[1]} columns")
        print(f"Columns: {list(df_clean.columns)}")
        print("\nSample data (first 15 rows):")
        print("-"*80)
        print(df_clean.head(15).to_string(index=True))
        print("\n")
    
    # Create a combined dataframe with all price data
    print("="*80)
    print("COMBINED PRICE DATA")
    print("="*80)
    
    all_prices = []
    
    for df in main_tables:
        df_clean = df.copy()
        df_clean = df_clean.loc[:, df_clean.columns.notna()]
        
        # Try to identify commodity and price columns
        for _, row in df_clean.iterrows():
            row_dict = row.to_dict()
            # Find the column with "COMMODITY" or first column
            commodity_col = [c for c in df_clean.columns if 'COMMODITY' in str(c).upper()]
            price_col = [c for c in df_clean.columns if 'PRICE' in str(c).upper()]
            spec_col = [c for c in df_clean.columns if 'SPECIFICATION' in str(c).upper()]
            
            if commodity_col and price_col:
                commodity = row[commodity_col[0]]
                price = row[price_col[0]] if price_col else None
                spec = row[spec_col[0]] if spec_col else None
                
                if commodity and str(commodity).strip() and commodity != 'COMMODITY':
                    all_prices.append({
                        'Commodity': str(commodity).strip(),
                        'Specification': str(spec).strip() if spec else '',
                        'Price (PHP)': str(price).strip() if price else 'n/a'
                    })
    
    if all_prices:
        combined_df = pd.DataFrame(all_prices)
        print(f"\nTotal price entries: {len(combined_df)}")
        print("\nFirst 20 entries:")
        print(combined_df.head(20).to_string(index=False))
        
        print("\n\nSample queries you could make:")
        print("-"*80)
        
        # Show some example products
        if len(combined_df) > 0:
            print("\nExample 1: Rice prices")
            rice = combined_df[combined_df['Commodity'].str.contains('Rice', case=False, na=False)]
            if len(rice) > 0:
                print(rice.head(10).to_string(index=False))
            
            print("\n\nExample 2: Vegetables")
            veggies = combined_df[combined_df['Commodity'].str.contains('Tomato|Eggplant|Cabbage', case=False, na=False)]
            if len(veggies) > 0:
                print(veggies.head(10).to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ DATA EXTRACTION COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Store this data in a database")
    print("2. Create search/query endpoints")
    print("3. Integrate with SMS for farmer queries")
    print("4. Example farmer query: 'Magkano ang kamatis sa NCR?'")
    print("   → System extracts: product='tomato', location='NCR'")
    print("   → Returns price from this dataset")


if __name__ == "__main__":
    main()
