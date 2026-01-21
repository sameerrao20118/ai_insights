"""
MySQL Database Schema Setup Script

This script creates the required MySQL database structure for AI Insights.
Run this script to set up your MySQL database before using the MySQL data source.
"""

-- Create database
CREATE DATABASE IF NOT EXISTS ai_insights
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ai_insights;

-- Create ai_usecases table
CREATE TABLE IF NOT EXISTS ai_usecases (
    -- Primary identifiers
    UseCaseID VARCHAR(50) PRIMARY KEY,
    UseCaseName VARCHAR(255) NOT NULL,
    FunctionID VARCHAR(50),
    
    -- Environment and team info
    Environment VARCHAR(50),
    Team VARCHAR(100) NOT NULL,
    KeyContact VARCHAR(255) NOT NULL,
    ProjectDescription TEXT NOT NULL,
    
    -- Financial metrics
    EstimatedBudgetGBP DECIMAL(15,2),
    BenefitValuePerAnnum DECIMAL(15,2),
    BenefitCostPerAnnum DECIMAL(15,2),
    ROIPerAnnum DECIMAL(15,2),
    BudgetOverrun BOOLEAN DEFAULT FALSE,
    
    -- AI platform details
    AIType VARCHAR(100),
    NumberOfUsers INT,
    UsageStartDate VARCHAR(50),
    
    -- Cost tracking
    CostToDateGBP DECIMAL(15,2),
    LastMonthCostGBP DECIMAL(15,2),
    LastThreeMonthsCostGBP DECIMAL(15,2),
    LastYearCostGBP DECIMAL(15,2),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    INDEX idx_environment (Environment),
    INDEX idx_team (Team),
    INDEX idx_ai_type (AIType),
    INDEX idx_roi (ROIPerAnnum)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample data insert (optional)
INSERT INTO ai_usecases (
    UseCaseID, UseCaseName, FunctionID, Environment, Team, KeyContact,
    ProjectDescription, EstimatedBudgetGBP, BenefitValuePerAnnum,
    AIType, NumberOfUsers
) VALUES (
    'UC001',
    'Customer Service Chatbot',
    'FN001',
    'Production',
    'Customer Experience',
    'john.doe@company.com',
    'AI-powered chatbot for customer support inquiries',
    250000.00,
    500000.00,
    'AI Gateway',
    5000
) ON DUPLICATE KEY UPDATE UseCaseID=UseCaseID;

-- Verify table creation
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ai_insights'
AND TABLE_NAME = 'ai_usecases';

-- Display column structure
DESCRIBE ai_usecases;
