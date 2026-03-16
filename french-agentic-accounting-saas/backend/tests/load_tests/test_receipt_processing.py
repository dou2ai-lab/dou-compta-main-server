# -----------------------------------------------------------------------------
# File: test_receipt_processing.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Load tests for receipt processing (5,000 receipts/day/company)
# -----------------------------------------------------------------------------

"""
Load Tests for Receipt Processing
Tests system capacity for 5,000 receipts per day per company
"""
import asyncio
import aiohttp
import time
from typing import List, Dict, Any
from datetime import datetime
import json

class ReceiptLoadTest:
    """Load test for receipt processing"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        api_token: str = "",
        tenant_id: str = ""
    ):
        self.base_url = base_url
        self.api_token = api_token
        self.tenant_id = tenant_id
        self.results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0,
            "avg_response_time": 0,
            "min_response_time": float('inf'),
            "max_response_time": 0,
            "errors": []
        }
    
    async def upload_receipt(
        self,
        session: aiohttp.ClientSession,
        receipt_data: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """Upload a single receipt"""
        start_time = time.time()
        
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('file', receipt_data, filename=filename, content_type='image/jpeg')
            form_data.add_field('tenant_id', self.tenant_id)
            
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }
            
            async with session.post(
                f"{self.base_url}/api/v1/receipts/upload",
                data=form_data,
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    return {
                        "success": True,
                        "response_time": response_time,
                        "receipt_id": result.get("id"),
                        "status_code": response.status
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "response_time": response_time,
                        "status_code": response.status,
                        "error": error_text
                    }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "response_time": response_time,
                "error": str(e)
            }
    
    async def run_load_test(
        self,
        num_receipts: int = 5000,
        concurrent_requests: int = 50,
        batch_size: int = 100
    ):
        """Run load test"""
        print(f"Starting load test: {num_receipts} receipts, {concurrent_requests} concurrent requests")
        
        # Generate test receipt data (dummy image)
        test_receipt_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb'
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Process in batches
            for batch_start in range(0, num_receipts, batch_size):
                batch_end = min(batch_start + batch_size, num_receipts)
                batch_num = batch_start // batch_size + 1
                
                print(f"Processing batch {batch_num}: receipts {batch_start} to {batch_end-1}")
                
                # Create tasks for concurrent uploads
                tasks = []
                for i in range(batch_start, batch_end):
                    filename = f"test_receipt_{i}.jpg"
                    task = self.upload_receipt(session, test_receipt_data, filename)
                    tasks.append(task)
                
                # Execute batch with concurrency limit
                semaphore = asyncio.Semaphore(concurrent_requests)
                
                async def bounded_upload(task):
                    async with semaphore:
                        return await task
                
                batch_results = await asyncio.gather(*[bounded_upload(task) for task in tasks])
                
                # Process results
                for result in batch_results:
                    self.results["total_requests"] += 1
                    if result["success"]:
                        self.results["successful"] += 1
                    else:
                        self.results["failed"] += 1
                        self.results["errors"].append(result.get("error", "Unknown error"))
                    
                    response_time = result["response_time"]
                    self.results["total_time"] += response_time
                    self.results["min_response_time"] = min(self.results["min_response_time"], response_time)
                    self.results["max_response_time"] = max(self.results["max_response_time"], response_time)
                
                # Print batch summary
                batch_success = sum(1 for r in batch_results if r["success"])
                print(f"Batch {batch_num} complete: {batch_success}/{len(batch_results)} successful")
        
        total_time = time.time() - start_time
        self.results["total_time"] = total_time
        self.results["avg_response_time"] = self.results["total_time"] / self.results["total_requests"] if self.results["total_requests"] > 0 else 0
        
        # Print final results
        self.print_results()
    
    def print_results(self):
        """Print test results"""
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        print(f"Total Requests: {self.results['total_requests']}")
        print(f"Successful: {self.results['successful']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['successful']/self.results['total_requests']*100):.2f}%")
        print(f"Total Time: {self.results['total_time']:.2f} seconds")
        print(f"Average Response Time: {self.results['avg_response_time']:.3f} seconds")
        print(f"Min Response Time: {self.results['min_response_time']:.3f} seconds")
        print(f"Max Response Time: {self.results['max_response_time']:.3f} seconds")
        print(f"Throughput: {self.results['total_requests']/self.results['total_time']:.2f} requests/second")
        
        if self.results["errors"]:
            print(f"\nErrors ({len(self.results['errors'])}):")
            error_counts = {}
            for error in self.results["errors"]:
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in error_counts.items():
                print(f"  {error}: {count}")
        
        print("="*60)
        
        # Calculate if system can handle 5,000 receipts/day
        receipts_per_second = self.results['total_requests'] / self.results['total_time']
        receipts_per_day = receipts_per_second * 86400  # seconds in a day
        
        print(f"\nCAPACITY ANALYSIS:")
        print(f"Current Throughput: {receipts_per_day:.0f} receipts/day")
        print(f"Target: 5,000 receipts/day")
        
        if receipts_per_day >= 5000:
            print("✓ System can handle 5,000 receipts/day")
        else:
            print("✗ System needs optimization to handle 5,000 receipts/day")
            print(f"  Required improvement: {(5000/receipts_per_day):.2f}x")

async def main():
    """Main function to run load test"""
    # Configuration
    BASE_URL = "http://localhost:8001"
    API_TOKEN = ""  # Set your API token
    TENANT_ID = ""  # Set your tenant ID
    
    # Run load test
    test = ReceiptLoadTest(
        base_url=BASE_URL,
        api_token=API_TOKEN,
        tenant_id=TENANT_ID
    )
    
    # Test with 5,000 receipts
    await test.run_load_test(
        num_receipts=5000,
        concurrent_requests=50,
        batch_size=100
    )

if __name__ == "__main__":
    asyncio.run(main())




