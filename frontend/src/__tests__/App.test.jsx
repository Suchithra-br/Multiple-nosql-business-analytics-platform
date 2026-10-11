import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App.jsx';
import Dashboard from '../pages/Dashboard.jsx';
import Analytics from '../pages/Analytics.jsx';
import LoadingState from '../components/LoadingState.jsx';
import { api } from '../services/api.js';

// Mock Recharts ResponsiveContainer to ensure SVG charts render inside JSDOM
vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => (
      <div data-testid="recharts-responsive-container" style={{ width: 800, height: 400 }}>
        {children}
      </div>
    ),
  };
});

// Mock API service methods with realistic verified dataset numbers
vi.mock('../services/api.js', () => ({
  api: {
    getHealth: vi.fn(),
    getOverview: vi.fn(),
    getMonthlySales: vi.fn(),
    getRegions: vi.fn(),
    getCategories: vi.fn(),
    getSegments: vi.fn(),
    getShipping: vi.fn(),
    getSubcategories: vi.fn(),
    getStates: vi.fn(),
    getTopProducts: vi.fn(),
    getTopCustomers: vi.fn(),
    searchCustomers: vi.fn(),
    searchOrders: vi.fn(),
    getOrderById: vi.fn(),
    getCustomerById: vi.fn(),
    getSalesByDate: vi.fn(),
    getSalesByRegionDate: vi.fn(),
    getSalesByCategoryDate: vi.fn(),
    getCustomerOrdersGraph: vi.fn(),
    getCustomerProductsGraph: vi.fn(),
    getProductCoPurchases: vi.fn(),
    getRegionCategoriesGraph: vi.fn(),
  },
}));

describe('Superstore Sales Analytics Platform — React Frontend Test Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations returning verified Phase 1-8 dataset numbers
    api.getHealth.mockResolvedValue({
      status: 'healthy',
      databases: { mongodb: 'healthy', redis: 'healthy', cassandra: 'healthy', neo4j: 'healthy' },
    });

    api.getOverview.mockResolvedValue({
      total_sales: 2261536.7827,
      total_orders: 4922,
      average_order_value: 459.475169,
      average_shipping_days: 4.0,
      yoy_sales_growth: 20.3,
      yoy_orders_growth: 28.3,
      yoy_aov_growth: -6.2,
      comparison_label: '2018 vs 2017',
      last_refreshed_at: '2026-10-11T12:00:00Z',
    });

    api.getMonthlySales.mockResolvedValue([
      { year_month: '2015-01', total_sales: 14236.90 },
      { year_month: '2015-02', total_sales: 4519.89 },
      { year_month: '2018-11', total_sales: 117935.10 },
      { year_month: '2018-12', total_sales: 83829.60 },
    ]);

    api.getRegions.mockResolvedValue([
      { region: 'West', total_sales: 710219.68 },
      { region: 'East', total_sales: 669518.73 },
      { region: 'Central', total_sales: 492646.91 },
      { region: 'South', total_sales: 389151.46 },
    ]);

    api.getCategories.mockResolvedValue([
      { category: 'Technology', total_sales: 827455.87 },
      { category: 'Furniture', total_sales: 728658.58 },
      { category: 'Office Supplies', total_sales: 705422.33 },
    ]);

    api.getSegments.mockResolvedValue([
      { segment: 'Consumer', total_sales: 1148060.54 },
      { segment: 'Corporate', total_sales: 688494.07 },
      { segment: 'Home Office', total_sales: 424982.17 },
    ]);

    api.getShipping.mockResolvedValue([
      { ship_mode: 'Standard Class', total_sales: 1340831.31 },
      { ship_mode: 'Second Class', total_sales: 449914.18 },
      { ship_mode: 'First Class', total_sales: 345572.34 },
      { ship_mode: 'Same Day', total_sales: 125218.95 },
    ]);

    api.getSubcategories.mockResolvedValue([
      { sub_category: 'Phones', category: 'Technology', total_sales: 327782.45 },
      { sub_category: 'Chairs', category: 'Furniture', total_sales: 322822.73 },
      { sub_category: 'Storage', category: 'Office Supplies', total_sales: 219343.39 },
      { sub_category: 'Tables', category: 'Furniture', total_sales: 202810.63 },
    ]);

    api.getStates.mockResolvedValue([
      { state: 'California', region: 'West', total_sales: 446306.46, order_count: 1002 },
      { state: 'New York', region: 'East', total_sales: 306361.15, order_count: 547 },
      { state: 'Texas', region: 'Central', total_sales: 168572.53, order_count: 480 },
    ]);

    api.getTopProducts.mockResolvedValue([
      {
        product_id: 'TEC-CO-10004722',
        product_name: 'Canon imageCLASS 2200 Advanced Copier',
        total_sales: 61599.82,
      },
      {
        product_id: 'OFF-BI-10003527',
        product_name: 'Fellowes PB500 Electric Punch Plastic Comb Binding Machine',
        total_sales: 27453.38,
      },
    ]);

    api.getTopCustomers.mockResolvedValue([
      {
        customer_id: 'SM-20320',
        customer_name: 'Sean Miller',
        total_spend: 25043.05,
      },
      {
        customer_id: 'TC-20980',
        customer_name: 'Tamara Chand',
        total_spend: 19052.22,
      },
    ]);

    api.searchCustomers.mockResolvedValue([
      { customer_id: 'CG-12520', customer_name: 'Claire Gute', segment: 'Consumer', primary_region: 'South' },
    ]);

    api.searchOrders.mockResolvedValue([
      { order_id: 'CA-2017-152156', order_date: '2017-11-08', customer_name: 'Claire Gute', order_total: 993.9 },
    ]);
  });

  // Test 1: Brand title and navigation renaming
  it('1. Dashboard renders main navigation, headers, and view container', async () => {
    render(<App />);
    expect(screen.getByText('Superstore Sales Analytics')).toBeInTheDocument();
    expect(screen.getByText(/Historical sales 2015–2018/i)).toBeInTheDocument();
    expect(screen.getByText('API connected')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Query Explorer' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
  });

  // Test 2: KPI values loaded from API
  it('2. KPI cards load and display verified business values from FastAPI overview endpoint', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('$2,261,536.78')).toBeInTheDocument();
      expect(screen.getByText('4,922')).toBeInTheDocument();
      expect(screen.getByText('$459.48')).toBeInTheDocument();
    });
    expect(api.getOverview).toHaveBeenCalled();
  });

  // Test 3: Monthly chart receives API data and supports year filter
  it('3. Monthly sales chart receives API data and triggers year-filtered queries', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(api.getMonthlySales).toHaveBeenCalledWith(null);
    });

    const select = screen.getByLabelText(/Filter Year:/i);
    expect(select).toBeInTheDocument();

    fireEvent.change(select, { target: { value: '2017' } });
    await waitFor(() => {
      expect(api.getMonthlySales).toHaveBeenCalledWith(2017);
    });
  });

  // Test 4: Region chart receives API data
  it('4. Regional sales section receives API data for West, East, Central, South', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Regional Sales')).toBeInTheDocument();
      expect(api.getRegions).toHaveBeenCalled();
    });
  });

  // Test 5: Category chart receives API data
  it('5. Category sales section receives API data for Technology, Furniture, Office Supplies', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Category Sales')).toBeInTheDocument();
      expect(api.getCategories).toHaveBeenCalled();
    });
  });

  // Test 6: Top products table renders
  it('6. Top products table renders ranked product records with real names and sales', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Canon imageCLASS 2200 Advanced Copier')).toBeInTheDocument();
      expect(screen.getByText('$61,599.82')).toBeInTheDocument();
      expect(screen.getByText('TEC-CO-10004722')).toBeInTheDocument();
    });
  });

  // Test 7: Top customers table renders
  it('7. Top customers table renders ranked customer records with real spend', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Sean Miller')).toBeInTheDocument();
      expect(screen.getByText('$25,043.05')).toBeInTheDocument();
      expect(screen.getByText('SM-20320')).toBeInTheDocument();
    });
  });

  // Test 8: Loading state renders cleanly
  it('8. Loading state component displays clean spinner and accessible text', () => {
    render(<LoadingState message="Fetching sales records..." />);
    expect(screen.getByText('Fetching sales records...')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  // Test 9: API error state handled gracefully
  it('9. Dashboard handles API error gracefully without crashing or showing fake data', async () => {
    api.getOverview.mockRejectedValueOnce(new Error('FastAPI server connection refused'));
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getAllByText('$0.00').length).toBeGreaterThanOrEqual(1);
    });
  });

  // Test 10: Navigation between Overview and Query Explorer
  it('10. Navigation between Overview and Query Explorer views functions correctly', async () => {
    render(<App />);

    const analyticsBtn = screen.getByRole('button', { name: 'Query Explorer' });
    fireEvent.click(analyticsBtn);

    expect(screen.getByText('Interactive Multi-NoSQL Query Explorer')).toBeInTheDocument();
    expect(screen.getByText('Executive KPI Cache')).toBeInTheDocument();

    const dashboardBtn = screen.getByRole('button', { name: 'Overview' });
    fireEvent.click(dashboardBtn);

    expect(screen.getByText('Executive Sales Overview & Business Insights')).toBeInTheDocument();
  });

  // Test 11: MongoDB order lookup works
  it('11. Operational order lookup retrieves and renders order document and nested items', async () => {
    api.getOrderById.mockResolvedValueOnce({
      order_id: 'CA-2017-152156',
      order_date: '2017-11-08',
      ship_date: '2017-11-11',
      ship_mode: 'Second Class',
      shipping_days: 3,
      customer: { customer_id: 'CG-12520', customer_name: 'Claire Gute', segment: 'Consumer' },
      shipping_address: { country: 'United States', city: 'Henderson', state: 'Kentucky', postal_code: '42420', region: 'South' },
      items: [
        { row_id: 1, product_id: 'FUR-BO-10001798', product_name: 'Bush Somerset Collection Bookcase', category: 'Furniture', sub_category: 'Bookcases', sales: 261.96 },
      ],
      order_total: 261.96,
      order_year: 2017,
      order_month: 11,
      order_quarter: 'Q4',
      order_year_month: '2017-11',
    });

    render(<Analytics />);

    const searchBtn = screen.getByRole('button', { name: 'Lookup Order' });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(api.getOrderById).toHaveBeenCalledWith('CA-2017-152156');
      expect(screen.getByText('Claire Gute (Consumer)')).toBeInTheDocument();
      expect(screen.getByText('Bush Somerset Collection Bookcase')).toBeInTheDocument();
      expect(screen.getAllByText('$261.96').length).toBeGreaterThanOrEqual(1);
    });
  });

  // Test 12: MongoDB customer lookup works
  it('12. Customer profile lookup retrieves customer record and statistics', async () => {
    api.getCustomerById.mockResolvedValueOnce({
      customer_id: 'CG-12520',
      customer_name: 'Claire Gute',
      segment: 'Consumer',
      primary_region: 'South',
      order_count: 5,
      total_spend: 1148.24,
      first_order_date: '2016-01-15',
      last_order_date: '2018-10-22',
    });

    render(<Analytics />);

    const searchBtn = screen.getByRole('button', { name: 'Lookup Customer' });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(api.getCustomerById).toHaveBeenCalledWith('CG-12520');
      expect(screen.getByText('Claire Gute')).toBeInTheDocument();
      expect(screen.getAllByText('South').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('$1,148.24')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  // Test 13: Cassandra date-based lookup works
  it('13. Cassandra daily sales query retrieves and displays point-in-time transactions', async () => {
    api.getSalesByDate.mockResolvedValueOnce([
      {
        order_date: '2017-11-08',
        order_id: 'CA-2017-152156',
        row_id: 1,
        product_id: 'FUR-BO-10001798',
        category: 'Furniture',
        sub_category: 'Bookcases',
        region: 'South',
        sales: 261.96,
      },
    ]);

    render(<Analytics />);

    const fetchDateBtn = screen.getByRole('button', { name: 'Fetch Date' });
    fireEvent.click(fetchDateBtn);

    await waitFor(() => {
      expect(api.getSalesByDate).toHaveBeenCalledWith('2017-11-08');
      expect(screen.getByText('Bookcases')).toBeInTheDocument();
    });
  });

  // Test 14: Cassandra date range validation catches start > end
  it('14. Cassandra region-date query validates start_date <= end_date before request', async () => {
    const { container } = render(<Analytics />);

    const startDateInput = container.querySelector('#region-start-date');
    const endDateInput = container.querySelector('#region-end-date');

    fireEvent.change(startDateInput, { target: { value: '2018-05-10' } });
    fireEvent.change(endDateInput, { target: { value: '2018-05-01' } });

    const queryBtn = screen.getByRole('button', { name: 'Query Region Range' });
    fireEvent.click(queryBtn);

    await waitFor(() => {
      expect(screen.getByText('Start date must be less than or equal to end date.')).toBeInTheDocument();
      expect(api.getSalesByRegionDate).not.toHaveBeenCalled();
    });
  });

  // Test 15: Neo4j customer graph traversal works
  it('15. Neo4j customer graph traversal retrieves order history and product affinities', async () => {
    api.getCustomerOrdersGraph.mockResolvedValueOnce([
      { order_id: 'CA-2017-152156', order_date: '2017-11-08', ship_mode: 'Second Class' },
    ]);
    api.getCustomerProductsGraph.mockResolvedValueOnce([
      { product_id: 'FUR-BO-10001798', product_name: 'Bush Somerset Bookcase', purchase_count: 2, total_spent: 523.92 },
    ]);

    render(<Analytics />);

    const graphBtn = screen.getByRole('button', { name: 'Traverse Graph' });
    fireEvent.click(graphBtn);

    await waitFor(() => {
      expect(api.getCustomerOrdersGraph).toHaveBeenCalledWith('CG-12520');
      expect(api.getCustomerProductsGraph).toHaveBeenCalledWith('CG-12520');
      expect(screen.getByText('Connected Orders (1)')).toBeInTheDocument();
      expect(screen.getByText('Bush Somerset Bookcase')).toBeInTheDocument();
    });
  });

  // Test 16: Neo4j product co-purchasing works
  it('16. Neo4j co-purchasing query displays frequently co-purchased items', async () => {
    api.getProductCoPurchases.mockResolvedValueOnce([
      { product_id: 'FUR-CH-10000454', product_name: 'Mitel 5320 IP Phone', times_co_purchased: 4 },
    ]);

    render(<Analytics />);

    const copurchaseBtn = screen.getByRole('button', { name: 'Find Co-Purchases' });
    fireEvent.click(copurchaseBtn);

    await waitFor(() => {
      expect(api.getProductCoPurchases).toHaveBeenCalledWith('FUR-BO-10001798', 10);
      expect(screen.getByText('Mitel 5320 IP Phone')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('Count')).toBeInTheDocument();
    });
  });

  // Test 17: Neo4j regional taxonomy hierarchy works
  it('17. Neo4j regional taxonomy 6-hop graph queries display category totals', async () => {
    api.getRegionCategoriesGraph.mockResolvedValueOnce([
      { category: 'Technology', item_count: 500, total_sales: 250000.0 },
      { category: 'Furniture', item_count: 400, total_sales: 240000.0 },
    ]);

    render(<Analytics />);

    const regionGraphBtn = screen.getByRole('button', { name: 'Traverse Region Hierarchy' });
    fireEvent.click(regionGraphBtn);

    await waitFor(() => {
      expect(api.getRegionCategoriesGraph).toHaveBeenCalledWith('West');
      expect(screen.getByText('Line Items')).toBeInTheDocument();
      expect(screen.getByText('500')).toBeInTheDocument();
    });
  });

  // Test 18: Invalid/missing lookup error handled cleanly
  it('18. Non-existent order lookup displays clear error state without crashing', async () => {
    api.getOrderById.mockRejectedValueOnce(new Error("Order 'INVALID-999' not found"));

    render(<Analytics />);

    const input = screen.getByLabelText('Order ID:');
    fireEvent.change(input, { target: { value: 'INVALID-999' } });

    const searchBtn = screen.getByRole('button', { name: 'Lookup Order' });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(screen.getByText("Order 'INVALID-999' not found")).toBeInTheDocument();
    });
  });

  // Test 19: Global Region and Year Filter selection
  it('19. Global filters allow selecting both Year and Region', async () => {
    render(<Dashboard />);

    const regionSelect = screen.getByLabelText(/Filter Region:/i);
    expect(regionSelect).toBeInTheDocument();

    fireEvent.change(regionSelect, { target: { value: 'West' } });

    await waitFor(() => {
      expect(screen.getByText(/Filtered: All Years · West/i)).toBeInTheDocument();
    });

    const resetBtn = screen.getByRole('button', { name: 'Reset Filters' });
    expect(resetBtn).toBeInTheDocument();
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(screen.getByText(/All 4,922 Orders \(Complete Dataset\)/i)).toBeInTheDocument();
    });
  });

  // Test 20: KPI cards render YoY context and Average Shipping Time
  it('20. KPI cards display YoY growth comparisons and Average Shipping Time metric', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('+20.3% vs 2017')).toBeInTheDocument();
      expect(screen.getByText('+28.3% vs 2017')).toBeInTheDocument();
      expect(screen.getByText('-6.2% vs 2017')).toBeInTheDocument();
      expect(screen.getByText('4.0 days')).toBeInTheDocument();
      expect(screen.getByText('AVG SHIPPING TIME')).toBeInTheDocument();
    });
  });

  // Test 21: "At a Glance" insight strip renders real analytical highlights
  it('21. At a Glance insight strip displays actual data-driven business statements', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('AT A GLANCE — BUSINESS INSIGHTS')).toBeInTheDocument();
      expect(screen.getByText(/West leads regional sales/i)).toBeInTheDocument();
      expect(screen.getByText(/Technology is the highest-revenue category/i)).toBeInTheDocument();
      expect(screen.getByText(/Average order fulfillment takes/i)).toBeInTheDocument();
    });
  });

  // Test 22: Sub-category analytics renders 17 sub-categories
  it('22. Sub-Category ranked view renders merchandise items with sales', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Sales by Sub-Category (All 17 Lines)')).toBeInTheDocument();
      expect(screen.getByText('Phones')).toBeInTheDocument();
      expect(screen.getByText('$327,782.45')).toBeInTheDocument();
      expect(screen.getByText('Chairs')).toBeInTheDocument();
    });
  });

  // Test 23: Geographic detail view renders top states table
  it('23. Geographic detail section renders top states table with order counts', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Top 10 States by Sales Volume')).toBeInTheDocument();
      expect(screen.getByText('California')).toBeInTheDocument();
      expect(screen.getByText('$446,306.46')).toBeInTheDocument();
      expect(screen.getByText('New York')).toBeInTheDocument();
    });
  });

  // Test 24: Customer search autocomplete shows suggestions
  it('24. Customer search in Query Explorer displays autocomplete suggestions', async () => {
    const { container } = render(<Analytics />);
    const input = container.querySelector('#customer-id-input');
    fireEvent.change(input, { target: { value: 'Claire' } });

    await waitFor(() => {
      expect(api.searchCustomers).toHaveBeenCalledWith('Claire', 5);
      expect(screen.getByText('Available Customers:')).toBeInTheDocument();
    });
  });

  // Test 25: CSV export buttons render on tables
  it('25. Result tables render Export CSV buttons for data download', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      const exportBtns = screen.getAllByRole('button', { name: /Export CSV/i });
      expect(exportBtns.length).toBeGreaterThanOrEqual(1);
    });
  });
});
