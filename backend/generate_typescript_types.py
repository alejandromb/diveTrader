#!/usr/bin/env python3
"""
Generate TypeScript types from SQLModel schemas
Fetches JSON schemas from the running API and converts them to TypeScript interfaces
"""

import requests
import json
import re
from typing import Dict, Any
from datetime import datetime

def json_schema_to_typescript(schema: Dict[str, Any], interface_name: str) -> str:
    """Convert a JSON schema to a TypeScript interface"""
    
    def map_type(json_type: str, json_format: str = None) -> str:
        """Map JSON schema types to TypeScript types"""
        type_mapping = {
            "string": "string",
            "integer": "number", 
            "number": "number",
            "boolean": "boolean",
            "array": "Array<any>",  # Will be refined based on items
            "object": "Record<string, any>"
        }
        
        if json_format == "date-time":
            return "string"  # ISO date strings
            
        return type_mapping.get(json_type, "any")
    
    def process_property(prop_name: str, prop_schema: Dict[str, Any]) -> str:
        """Process a single property and return TypeScript field definition"""
        prop_type = prop_schema.get("type", "any")
        prop_format = prop_schema.get("format")
        
        # Handle enums
        if "enum" in prop_schema:
            enum_values = [f'"{val}"' for val in prop_schema["enum"]]
            ts_type = " | ".join(enum_values)
            # Special case for investment_frequency - use the enum type
            if prop_name == "investment_frequency":
                ts_type = "InvestmentFrequency"
        # Handle allOf patterns (often used for enum references)
        elif "allOf" in prop_schema:
            # Check if it's referencing an enum
            all_of = prop_schema["allOf"][0] if prop_schema["allOf"] else {}
            if "$ref" in all_of and "InvestmentFrequencyEnum" in all_of["$ref"]:
                ts_type = "InvestmentFrequency"
            else:
                ts_type = map_type(prop_type, prop_format)
        # Handle arrays
        elif prop_type == "array" and "items" in prop_schema:
            items_type = map_type(prop_schema["items"].get("type", "any"))
            ts_type = f"Array<{items_type}>"
        else:
            ts_type = map_type(prop_type, prop_format)
        
        # Check if property is required
        required_props = schema.get("required", [])
        optional = "?" if prop_name not in required_props else ""
        
        # Add description as comment if available
        description = prop_schema.get("description", "")
        comment = f"  /** {description} */\n" if description else ""
        
        return f"{comment}  {prop_name}{optional}: {ts_type};"
    
    # Generate interface
    properties = schema.get("properties", {})
    fields = []
    
    for prop_name, prop_schema in properties.items():
        field_def = process_property(prop_name, prop_schema)
        fields.append(field_def)
    
    interface_body = "\n".join(fields)
    
    # Add schema description as interface comment
    schema_desc = schema.get("description", f"Generated from {interface_name} SQLModel")
    
    return f"""/**
 * {schema_desc}
 * Generated from SQLModel schema on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */
export interface {interface_name} {{
{interface_body}
}}"""

def generate_enum_types(base_url: str) -> str:
    """Generate TypeScript enums from API endpoints"""
    
    enums_code = []
    
    # Strategy Types enum
    try:
        response = requests.get(f"{base_url}/api/v2/strategies/enums/strategy-types")
        if response.status_code == 200:
            strategy_types = response.json()
            enum_values = [f'  {item["name"]} = "{item["value"]}"' for item in strategy_types]
            enum_body = ",\n".join(enum_values)
            
            enums_code.append(f"""/**
 * Available strategy types
 */
export enum StrategyType {{
{enum_body}
}}""")
    except Exception as e:
        print(f"Warning: Could not fetch strategy types: {e}")
    
    # Investment Frequencies enum
    try:
        response = requests.get(f"{base_url}/api/v2/strategies/enums/investment-frequencies")
        if response.status_code == 200:
            frequencies = response.json()
            enum_values = [f'  {item["name"]} = "{item["value"]}"' for item in frequencies]
            enum_body = ",\n".join(enum_values)
            
            enums_code.append(f"""/**
 * Available investment frequencies
 */
export enum InvestmentFrequency {{
{enum_body}
}}""")
    except Exception as e:
        print(f"Warning: Could not fetch investment frequencies: {e}")
    
    return "\n\n".join(enums_code)

def main():
    """Generate TypeScript types from running SQLModel API"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Generating TypeScript types from SQLModel schemas...")
    print("=" * 60)
    
    # Test API connectivity
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not healthy: {response.status_code}")
            return 1
        print("✅ API connection successful")
    except Exception as e:
        print(f"❌ Cannot connect to API at {base_url}: {e}")
        print("Make sure the SQLModel server is running (python3 main_sqlmodel.py)")
        return 1
    
    typescript_code = []
    
    # Generate enums first
    print("\n📝 Generating enums...")
    enums = generate_enum_types(base_url)
    if enums:
        typescript_code.append(enums)
        print("✅ Enums generated")
    
    # Generate schemas
    schemas_to_fetch = [
        ("btc-settings", "BTCScalpingSettings"),
        ("portfolio-settings", "PortfolioDistributorSettings")
    ]
    
    print("\n📝 Generating interface schemas...")
    for schema_endpoint, interface_name in schemas_to_fetch:
        try:
            url = f"{base_url}/api/v2/strategies/schema/{schema_endpoint}"
            print(f"📍 Fetching: {url}")
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                schema = response.json()
                ts_interface = json_schema_to_typescript(schema, interface_name)
                typescript_code.append(ts_interface)
                print(f"✅ Generated {interface_name}")
            else:
                print(f"❌ Failed to fetch {schema_endpoint}: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error generating {interface_name}: {e}")
    
    # Generate Strategy response interface (from API response structure)
    print("\n📝 Generating Strategy response interface...")
    try:
        response = requests.get(f"{base_url}/api/v2/strategies/")
        if response.status_code == 200:
            strategies = response.json()
            if strategies:
                # Use first strategy as template for interface
                strategy = strategies[0]
                
                strategy_interface = f"""/**
 * Strategy response from API
 * Generated from API response structure on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */
export interface Strategy {{
  id: number;
  name: string;
  strategy_type: StrategyType;
  is_active: boolean;
  initial_capital: number;
  current_capital: number;
  created_at: string;
  updated_at: string;
  config?: string;
  is_running?: boolean;
}}"""
                typescript_code.append(strategy_interface)
                print("✅ Generated Strategy interface")
    except Exception as e:
        print(f"❌ Error generating Strategy interface: {e}")
    
    # Combine all TypeScript code
    if typescript_code:
        full_typescript = f"""// Auto-generated TypeScript types from DiveTrader SQLModel schemas
// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// DO NOT EDIT - This file is automatically generated

{chr(10).join(typescript_code)}

// API Response wrapper types
export interface ApiResponse<T> {{
  data?: T;
  error?: string;
  message?: string;
}}

export interface StrategyListResponse extends ApiResponse<Strategy[]> {{}}
export interface StrategyResponse extends ApiResponse<Strategy> {{}}
export interface BTCSettingsResponse extends ApiResponse<BTCScalpingSettings> {{}}
export interface PortfolioSettingsResponse extends ApiResponse<PortfolioDistributorSettings> {{}}
"""
        
        # Write to file
        output_file = "/Users/alejandromenabrito/Documents/code/diveTrader/frontend/src/types/api.ts"
        try:
            with open(output_file, 'w') as f:
                f.write(full_typescript)
            print(f"\n🎉 TypeScript types written to: {output_file}")
            print(f"📊 Generated {len(typescript_code)} interfaces/enums")
            return 0
        except Exception as e:
            print(f"❌ Error writing to file: {e}")
            print("\nGenerated TypeScript code:")
            print("=" * 60)
            print(full_typescript)
            return 1
    else:
        print("❌ No TypeScript code generated")
        return 1

if __name__ == "__main__":
    exit(main())