from HelpServiceState import run_help_service

# ============================================================================
# TEST EXAMPLES
# ============================================================================

if __name__ == "__main__":
    #print_graph_structure()
    
    # print("\n" + "="*70)
    # print("TEST 1: Simple Query")
    # print("="*70)
    # response = run_help_service("Amanda Lee", "Show my employee info")
    # print(response)
    
    # print("\n" + "="*70)
    # print("TEST 2: Update Request")
    # print("="*70)
    # response = run_help_service("Sarah Johnson", "I am not able to login");
    # print("="*70)
    # print("the response is ",response)
    
    # print("\n" + "="*70)
    # print("TEST 3: Apply Leave User")
    # print("="*70)
    # response = run_help_service("James Garcia", "I am not able to apply for leaves for 2 days")
    # print("="*70)
    # print(response)
    
    # print("\n" + "="*70)
    # print("TEST 4: Complex Query")
    # print("="*70)
    # response = run_help_service("David Wilson", "I want to change my department from Sales to Marketing?")
    # print(response)

    print("\n" + "="*70)
    print("TEST : Insert Attendance")
    print("="*70)
    response = run_help_service("Sarah Johnson", "Please insert my attendance for today");
    print("="*70)
    print("the response is ",response)