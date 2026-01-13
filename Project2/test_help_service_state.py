"""
Unit Tests for HelpServiceState.py
Tests all functions in the A2A Help Service System
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import date
from typing import Dict, Any

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock external dependencies before importing the module
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['langchain_ollama'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.messages'] = MagicMock()

from HelpServiceState import (
    HelpServiceState,
    MCPClient,
    validate_user,
    classify_issue,
    route_issue,
    fetch_simple_data,
    handle_update,
    verify_update,
    handle_complex,
    format_response,
    mcp_client
)


class TestMCPClient(unittest.TestCase):
    """Test the MCPClient class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = MCPClient()
    
    def test_query_employees_all(self):
        """Test querying all employees"""
        result = self.client.query("employees")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "John Doe")
        self.assertEqual(result[1]["name"], "Jane Smith")
    
    def test_query_employees_by_email(self):
        """Test querying employees by email"""
        result = self.client.query("employees", {"email": "john@company.com"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "John Doe")
    
    def test_query_employees_not_found(self):
        """Test querying non-existent employee"""
        result = self.client.query("employees", {"email": "notfound@company.com"})
        self.assertEqual(len(result), 0)
    
    def test_query_attendance_all(self):
        """Test querying all attendance records"""
        result = self.client.query("attendance")
        self.assertEqual(len(result), 2)
    
    def test_query_attendance_by_emp_id(self):
        """Test querying attendance by employee ID"""
        result = self.client.query("attendance", {"emp_id": 1})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["employee_name"], "John Doe")
    
    def test_query_invalid_table(self):
        """Test querying invalid table"""
        result = self.client.query("invalid_table")
        self.assertEqual(len(result), 0)
    
    def test_update_employee(self):
        """Test updating employee record"""
        success = self.client.update("employees", 1, {"leave_days": 25})
        self.assertTrue(success)
        
        # Verify update
        result = self.client.query("employees", {"id": 1})
        self.assertEqual(result[0]["leave_days"], 25)
    
    def test_update_nonexistent_record(self):
        """Test updating non-existent record"""
        success = self.client.update("employees", 999, {"leave_days": 25})
        self.assertFalse(success)
    
    def test_update_invalid_table(self):
        """Test updating invalid table"""
        success = self.client.update("invalid_table", 1, {"field": "value"})
        self.assertFalse(success)
    
    def test_insert_employee(self):
        """Test inserting new employee"""
        new_employee = {
            "name": "Bob Wilson",
            "email": "bob@company.com",
            "department": "Sales",
            "license": "PRO"
        }
        success = self.client.insert("employees", new_employee)
        self.assertTrue(success)
        
        # Verify insertion
        result = self.client.query("employees", {"email": "bob@company.com"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Bob Wilson")
    
    def test_insert_attendance(self):
        """Test inserting new attendance record"""
        new_attendance = {
            "emp_id": 1,
            "employee_name": "John Doe",
            "date": "2024-01-09",
            "check_in": "09:00",
            "check_out": "17:00"
        }
        success = self.client.insert("attendance", new_attendance)
        self.assertTrue(success)
    
    def test_insert_invalid_table(self):
        """Test inserting into invalid table"""
        success = self.client.insert("invalid_table", {"field": "value"})
        self.assertFalse(success)


class TestValidateUser(unittest.TestCase):
    """Test the validate_user function"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset mcp_client data before each test
        self.client = MCPClient()
    
    def test_validate_user_success(self):
        """Test successful user validation"""
        state = {
            "user_email": "john@company.com",
            "mcp_calls": 0
        }
        result = validate_user(state)
        
        self.assertIsNone(result.get("error_message"))
        self.assertEqual(result["user_id"], 1)
        self.assertIsNotNone(result["user_data"])
        self.assertEqual(result["mcp_calls"], 1)
    
    def test_validate_user_not_found(self):
        """Test validation with non-existent user"""
        state = {
            "user_email": "notfound@company.com",
            "mcp_calls": 0
        }
        result = validate_user(state)
        
        self.assertEqual(result["error_message"], "User not found")
        self.assertEqual(result["mcp_calls"], 1)
    
    def test_validate_user_not_verified(self):
        """Test validation with unverified user"""
        # Temporarily modify the mock data
        original_verified = mcp_client.employees[0]["verified"]
        mcp_client.employees[0]["verified"] = False
        
        state = {
            "user_email": "john@company.com",
            "mcp_calls": 0
        }
        result = validate_user(state)
        
        self.assertEqual(result["error_message"], "Email not verified")
        
        # Restore original data
        mcp_client.employees[0]["verified"] = original_verified
    
    def test_validate_user_inactive(self):
        """Test validation with inactive user"""
        original_active = mcp_client.employees[0]["active"]
        mcp_client.employees[0]["active"] = False
        
        state = {
            "user_email": "john@company.com",
            "mcp_calls": 0
        }
        result = validate_user(state)
        
        self.assertEqual(result["error_message"], "Account inactive")
        
        mcp_client.employees[0]["active"] = original_active
    
    def test_validate_user_license_inactive(self):
        """Test validation with inactive license"""
        original_license = mcp_client.employees[0]["license_active"]
        mcp_client.employees[0]["license_active"] = False
        
        state = {
            "user_email": "john@company.com",
            "mcp_calls": 0
        }
        result = validate_user(state)
        
        self.assertEqual(result["error_message"], "License inactive")
        
        mcp_client.employees[0]["license_active"] = original_license
    
    def test_validate_user_license_expired(self):
        """Test validation with expired license"""
        original_expired = mcp_client.employees[0]["license_expired"]
        mcp_client.employees[0]["license_expired"] = True
        
        state = {
            "user_email": "john@company.com",
            "mcp_calls": 0
        }
        result = validate_user(state)
        
        self.assertEqual(result["error_message"], "License expired")
        
        mcp_client.employees[0]["license_expired"] = original_expired


class TestClassifyIssue(unittest.TestCase):
    """Test the classify_issue function"""
    
    @patch('HelpServiceState.llm')
    def test_classify_query_employee(self, mock_llm):
        """Test classifying employee query"""
        mock_response = Mock()
        mock_response.content = '{"category": "query_employee", "params": {}}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_message": "Show me my employee information",
            "llm_calls": 0
        }
        result = classify_issue(state)
        
        self.assertEqual(result["issue_category"], "query_employee")
        self.assertEqual(result["llm_calls"], 1)
    
    @patch('HelpServiceState.llm')
    def test_classify_query_attendance(self, mock_llm):
        """Test classifying attendance query"""
        mock_response = Mock()
        mock_response.content = '{"category": "query_attendance", "params": {"date": "2024-01-08"}}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_message": "Show my attendance for 2024-01-08",
            "llm_calls": 0
        }
        result = classify_issue(state)
        
        self.assertEqual(result["issue_category"], "query_attendance")
        self.assertEqual(result["extracted_params"]["date"], "2024-01-08")
    
    @patch('HelpServiceState.llm')
    def test_classify_update_leave(self, mock_llm):
        """Test classifying leave update"""
        mock_response = Mock()
        mock_response.content = '{"category": "update_leave", "params": {"leave_days": 25}}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_message": "Update my leave days to 25",
            "llm_calls": 0
        }
        result = classify_issue(state)
        
        self.assertEqual(result["issue_category"], "update_leave")
        self.assertEqual(result["extracted_params"]["leave_days"], 25)
    
    @patch('HelpServiceState.llm')
    def test_classify_invalid_json(self, mock_llm):
        """Test handling invalid JSON response"""
        mock_response = Mock()
        mock_response.content = 'Invalid JSON'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_message": "Some message",
            "llm_calls": 0
        }
        result = classify_issue(state)
        
        # Should default to query_employee
        self.assertEqual(result["issue_category"], "query_employee")
        self.assertEqual(result["extracted_params"], {})


class TestRouteIssue(unittest.TestCase):
    """Test the route_issue function"""
    
    def test_route_with_error(self):
        """Test routing when error exists"""
        state = {
            "error_message": "Some error"
        }
        result = route_issue(state)
        self.assertEqual(result, "format_response")
    
    def test_route_query_employee(self):
        """Test routing query_employee"""
        state = {
            "issue_category": "query_employee"
        }
        result = route_issue(state)
        self.assertEqual(result, "fetch_simple_data")
    
    def test_route_query_attendance(self):
        """Test routing query_attendance"""
        state = {
            "issue_category": "query_attendance"
        }
        result = route_issue(state)
        self.assertEqual(result, "fetch_simple_data")
    
    def test_route_update_leave(self):
        """Test routing update_leave"""
        state = {
            "issue_category": "update_leave"
        }
        result = route_issue(state)
        self.assertEqual(result, "handle_update")
    
    def test_route_update_attendance(self):
        """Test routing update_attendance"""
        state = {
            "issue_category": "update_attendance"
        }
        result = route_issue(state)
        self.assertEqual(result, "handle_update")
    
    def test_route_complex_report(self):
        """Test routing complex_report"""
        state = {
            "issue_category": "complex_report"
        }
        result = route_issue(state)
        self.assertEqual(result, "handle_complex")
    
    def test_route_unknown_category(self):
        """Test routing unknown category"""
        state = {
            "issue_category": "unknown"
        }
        result = route_issue(state)
        self.assertEqual(result, "handle_complex")


class TestFetchSimpleData(unittest.TestCase):
    """Test the fetch_simple_data function"""
    
    def test_fetch_employee_data(self):
        """Test fetching employee data"""
        state = {
            "issue_category": "query_employee",
            "extracted_params": {},
            "user_id": 1,
            "mcp_calls": 0
        }
        result = fetch_simple_data(state)
        
        self.assertIsNotNone(result["db_result"])
        self.assertEqual(len(result["db_result"]), 1)
        self.assertEqual(result["db_result"][0]["name"], "John Doe")
        self.assertEqual(result["mcp_calls"], 1)
    
    def test_fetch_attendance_data(self):
        """Test fetching attendance data"""
        state = {
            "issue_category": "query_attendance",
            "extracted_params": {},
            "user_id": 1,
            "mcp_calls": 0
        }
        result = fetch_simple_data(state)
        
        self.assertIsNotNone(result["db_result"])
        self.assertEqual(len(result["db_result"]), 1)
        self.assertEqual(result["mcp_calls"], 1)
    
    def test_fetch_attendance_with_date(self):
        """Test fetching attendance data with date filter"""
        state = {
            "issue_category": "query_attendance",
            "extracted_params": {"date": "2024-01-08"},
            "user_id": 1,
            "mcp_calls": 0
        }
        result = fetch_simple_data(state)
        
        self.assertIsNotNone(result["db_result"])
        self.assertEqual(result["mcp_calls"], 1)
    
    def test_fetch_unknown_category(self):
        """Test fetching with unknown category"""
        state = {
            "issue_category": "unknown",
            "extracted_params": {},
            "user_id": 1,
            "mcp_calls": 0
        }
        result = fetch_simple_data(state)
        
        self.assertEqual(result["db_result"], [])


class TestHandleUpdate(unittest.TestCase):
    """Test the handle_update function"""
    
    @patch('HelpServiceState.llm')
    def test_handle_update_leave_success(self, mock_llm):
        """Test successful leave update"""
        mock_response = Mock()
        mock_response.content = '{"valid": true, "reason": "Valid"}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "issue_category": "update_leave",
            "extracted_params": {"leave_days": 25},
            "user_id": 1,
            "user_data": {"name": "John Doe", "id": 1},
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_update(state)
        
        self.assertEqual(result["action_result"], "Update successful")
        self.assertIsNone(result.get("error_message"))
        self.assertEqual(result["llm_calls"], 1)
        self.assertEqual(result["mcp_calls"], 2)
    
    @patch('HelpServiceState.llm')
    def test_handle_update_validation_failed(self, mock_llm):
        """Test update with validation failure"""
        mock_response = Mock()
        mock_response.content = '{"valid": false, "reason": "Invalid leave days"}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "issue_category": "update_leave",
            "extracted_params": {"leave_days": 50},
            "user_id": 1,
            "user_data": {"name": "John Doe", "id": 1},
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_update(state)
        
        self.assertEqual(result["error_message"], "Invalid leave days")
        self.assertIsNone(result.get("action_result"))
    
    @patch('HelpServiceState.llm')
    def test_handle_update_attendance_success(self, mock_llm):
        """Test successful attendance update"""
        mock_response = Mock()
        mock_response.content = '{"valid": true, "reason": "Valid"}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "issue_category": "update_attendance",
            "extracted_params": {
                "date": "2024-01-09",
                "check_in": "09:00",
                "check_out": "17:00"
            },
            "user_id": 1,
            "user_data": {"name": "John Doe", "id": 1},
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_update(state)
        
        self.assertEqual(result["action_result"], "Update successful")
        self.assertEqual(result["llm_calls"], 1)
        self.assertEqual(result["mcp_calls"], 2)
    
    @patch('HelpServiceState.llm')
    def test_handle_update_invalid_json(self, mock_llm):
        """Test update with invalid JSON validation response"""
        mock_response = Mock()
        mock_response.content = 'Invalid JSON'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "issue_category": "update_leave",
            "extracted_params": {"leave_days": 25},
            "user_id": 1,
            "user_data": {"name": "John Doe", "id": 1},
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_update(state)
        
        self.assertEqual(result["error_message"], "Validation failed")
    
    @patch('HelpServiceState.llm')
    def test_handle_update_unknown_category(self, mock_llm):
        """Test update with unknown category"""
        mock_response = Mock()
        mock_response.content = '{"valid": true, "reason": "Valid"}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "issue_category": "unknown",
            "extracted_params": {},
            "user_id": 1,
            "user_data": {"name": "John Doe", "id": 1},
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_update(state)
        
        self.assertEqual(result["error_message"], "Update failed")


class TestVerifyUpdate(unittest.TestCase):
    """Test the verify_update function"""
    
    def test_verify_update_success(self):
        """Test successful update verification"""
        state = {
            "user_id": 1,
            "mcp_calls": 0
        }
        result = verify_update(state)
        
        self.assertIsNotNone(result["db_result"])
        self.assertEqual(result["mcp_calls"], 1)
    
    def test_verify_update_with_error(self):
        """Test verification when error exists"""
        state = {
            "user_id": 1,
            "error_message": "Some error",
            "mcp_calls": 0
        }
        result = verify_update(state)
        
        # Should return early without incrementing mcp_calls
        self.assertEqual(result["mcp_calls"], 0)


class TestHandleComplex(unittest.TestCase):
    """Test the handle_complex function"""
    
    @patch('HelpServiceState.llm')
    def test_handle_complex_success(self, mock_llm):
        """Test successful complex query handling"""
        mock_response = Mock()
        mock_response.content = '{"answer": "Analysis result", "data": [1, 2, 3]}'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_message": "Generate monthly attendance report",
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_complex(state)
        
        self.assertIsNotNone(result["db_result"])
        self.assertEqual(result["db_result"]["answer"], "Analysis result")
        self.assertEqual(result["llm_calls"], 1)
        self.assertEqual(result["mcp_calls"], 2)
    
    @patch('HelpServiceState.llm')
    def test_handle_complex_invalid_json(self, mock_llm):
        """Test complex query with invalid JSON response"""
        mock_response = Mock()
        mock_response.content = 'Plain text answer'
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_message": "Generate report",
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = handle_complex(state)
        
        self.assertIsNotNone(result["db_result"])
        self.assertEqual(result["db_result"]["answer"], "Plain text answer")


class TestFormatResponse(unittest.TestCase):
    """Test the format_response function"""
    
    def test_format_response_error(self):
        """Test formatting error response"""
        state = {
            "error_message": "User not found",
            "llm_calls": 1,
            "mcp_calls": 2
        }
        result = format_response(state)
        
        self.assertIn("❌ Error: User not found", result["final_response"])
        self.assertIn("1 LLM calls", result["final_response"])
        self.assertIn("2 DB calls", result["final_response"])
    
    def test_format_response_action_result(self):
        """Test formatting action result"""
        state = {
            "action_result": "Update successful",
            "db_result": [{"id": 1, "name": "John"}],
            "llm_calls": 1,
            "mcp_calls": 3
        }
        result = format_response(state)
        
        self.assertIn("✅ Update successful", result["final_response"])
        self.assertIn("Updated data:", result["final_response"])
    
    def test_format_response_db_result(self):
        """Test formatting database result"""
        state = {
            "db_result": [{"id": 1, "name": "John Doe"}],
            "llm_calls": 1,
            "mcp_calls": 2
        }
        result = format_response(state)
        
        self.assertIn("📊 Result:", result["final_response"])
        self.assertIn("John Doe", result["final_response"])
    
    def test_format_response_default(self):
        """Test formatting default response"""
        state = {
            "llm_calls": 0,
            "mcp_calls": 0
        }
        result = format_response(state)
        
        self.assertIn("✅ Request processed", result["final_response"])
    
    def test_format_response_missing_counters(self):
        """Test formatting with missing counter values"""
        state = {}
        result = format_response(state)
        
        self.assertIn("0 LLM calls", result["final_response"])
        self.assertIn("0 DB calls", result["final_response"])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""
    
    @patch('HelpServiceState.llm')
    def test_complete_query_workflow(self, mock_llm):
        """Test complete workflow for query operation"""
        # Mock LLM for classification
        mock_response = Mock()
        mock_response.content = '{"category": "query_employee", "params": {}}'
        mock_llm.invoke.return_value = mock_response
        
        # 1. Validate user
        state = {
            "user_email": "john@company.com",
            "user_message": "Show my employee info",
            "llm_calls": 0,
            "mcp_calls": 0
        }
        state = validate_user(state)
        self.assertIsNone(state.get("error_message"))
        
        # 2. Classify issue
        state = classify_issue(state)
        self.assertEqual(state["issue_category"], "query_employee")
        
        # 3. Route issue
        route = route_issue(state)
        self.assertEqual(route, "fetch_simple_data")
        
        # 4. Fetch data
        state = fetch_simple_data(state)
        self.assertIsNotNone(state["db_result"])
        
        # 5. Format response
        state = format_response(state)
        self.assertIn("📊 Result:", state["final_response"])
    
    @patch('HelpServiceState.llm')
    def test_complete_update_workflow(self, mock_llm):
        """Test complete workflow for update operation"""
        # Mock LLM responses
        responses = [
            Mock(content='{"category": "update_leave", "params": {"leave_days": 25}}'),
            Mock(content='{"valid": true, "reason": "Valid"}')
        ]
        mock_llm.invoke.side_effect = responses
        
        # 1. Validate user
        state = {
            "user_email": "john@company.com",
            "user_message": "Update my leave to 25 days",
            "llm_calls": 0,
            "mcp_calls": 0
        }
        state = validate_user(state)
        
        # 2. Classify issue
        state = classify_issue(state)
        self.assertEqual(state["issue_category"], "update_leave")
        
        # 3. Route issue
        route = route_issue(state)
        self.assertEqual(route, "handle_update")
        
        # 4. Handle update
        state = handle_update(state)
        self.assertEqual(state["action_result"], "Update successful")
        
        # 5. Verify update
        state = verify_update(state)
        self.assertIsNotNone(state["db_result"])
        
        # 6. Format response
        state = format_response(state)
        self.assertIn("✅ Update successful", state["final_response"])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

