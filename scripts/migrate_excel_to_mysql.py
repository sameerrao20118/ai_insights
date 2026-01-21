#!/usr/bin/env python3
"""
Excel to MySQL Migration Script

This script helps migrate data from Excel files to MySQL database.
Usage: python migrate_excel_to_mysql.py
"""
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources.excel_source import ExcelSource
from data_sources.mysql_source import MySQLSource
from config import settings
from models import AIUseCase


def migrate_excel_to_mysql():
    """Migrate data from Excel to MySQL."""
    print("=" * 60)
    print("AI Insights - Excel to MySQL Migration")
    print("=" * 60)
    print()
    
    # Load from Excel
    print("📂 Loading data from Excel...")
    try:
        excel_source = ExcelSource()
        usecases = excel_source.load_all_usecases()
        print(f"✅ Loaded {len(usecases)} use cases from Excel")
    except Exception as e:
        print(f"❌ Error loading from Excel: {e}")
        return False
    
    if not usecases:
        print("⚠️ No use cases found in Excel file")
        return False
    
    # Connect to MySQL
    print("\n🔌 Connecting to MySQL...")
    print(f"   Host: {settings.mysql_host}")
    print(f"   Database: {settings.mysql_database}")
    print(f"   Table: {settings.mysql_table}")
    
    try:
        mysql_source = MySQLSource()
        if not mysql_source.validate_connection():
            print("❌ MySQL connection failed")
            print("   Check your .env file configuration")
            return False
        print("✅ MySQL connection successful")
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False
    
    # Insert data
    print(f"\n📥 Inserting {len(usecases)} use cases into MySQL...")
    
    connection = None
    cursor = None
    success_count = 0
    error_count = 0
    
    try:
        connection = mysql_source._get_connection()
        cursor = connection.cursor()
        
        for idx, uc in enumerate(usecases, 1):
            try:
                # Build INSERT query
                query = f"""
                    INSERT INTO {settings.mysql_table} (
                        UseCaseID, UseCaseName, FunctionID, Environment, Team,
                        KeyContact, ProjectDescription, EstimatedBudgetGBP,
                        BenefitValuePerAnnum, AIType, NumberOfUsers, UsageStartDate,
                        CostToDateGBP, LastMonthCostGBP, LastThreeMonthsCostGBP,
                        LastYearCostGBP, BenefitCostPerAnnum, ROIPerAnnum, BudgetOverrun
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        UseCaseName = VALUES(UseCaseName),
                        ProjectDescription = VALUES(ProjectDescription),
                        EstimatedBudgetGBP = VALUES(EstimatedBudgetGBP),
                        BenefitValuePerAnnum = VALUES(BenefitValuePerAnnum)
                """
                
                values = (
                    uc.UseCaseID,
                    uc.UseCaseName,
                    uc.FunctionID,
                    uc.Environment,
                    uc.Team,
                    uc.KeyContact,
                    uc.ProjectDescription,
                    uc.EstimatedBudgetGBP,
                    uc.BenefitValuePerAnnum,
                    uc.AIType,
                    uc.NumberOfUsers,
                    uc.UsageStartDate,
                    uc.CostToDateGBP,
                    uc.LastMonthCostGBP,
                    uc.LastThreeMonthsCostGBP,
                    uc.LastYearCostGBP,
                    uc.BenefitCostPerAnnum,
                    uc.ROIPerAnnum,
                    uc.BudgetOverrun,
                )
                
                cursor.execute(query, values)
                success_count += 1
                
                if idx % 10 == 0:
                    print(f"   Progress: {idx}/{len(usecases)}")
                    
            except Exception as e:
                error_count += 1
                print(f"   ⚠️ Error inserting {uc.UseCaseID}: {e}")
        
        # Commit transaction
        connection.commit()
        
        print(f"\n✅ Migration completed!")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def verify_migration():
    """Verify the migration by counting rows in MySQL."""
    print("\n🔍 Verifying migration...")
    
    try:
        mysql_source = MySQLSource()
        metadata = mysql_source.get_metadata()
        row_count = metadata.get("row_count", 0)
        
        print(f"✅ MySQL table contains {row_count} rows")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT:")
    print("   1. Make sure your .env file is configured for MySQL")
    print("   2. Ensure MySQL server is running")
    print("   3. Database and table should already exist (run setup_mysql_schema.sql first)")
    print()
    
    response = input("Continue with migration? (yes/no): ")
    
    if response.lower() not in ["yes", "y"]:
        print("Migration cancelled")
        sys.exit(0)
    
    success = migrate_excel_to_mysql()
    
    if success:
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("   You can now use DATA_SOURCE=mysql in your .env file")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
