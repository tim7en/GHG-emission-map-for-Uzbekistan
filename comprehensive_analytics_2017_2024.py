#!/usr/bin/env python3
"""
Comprehensive Atmospheric Analytics for Uzbekistan (2017-2024)
Multi-year analysis with visualization, mapping, and trend analysis

Author: AlphaEarth Analysis Team
Date: August 15, 2025
"""

import ee
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import folium
from folium import plugins
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def comprehensive_analytics_2017_2024():
    """Comprehensive 8-year atmospheric analysis with visualization"""
    
    print("📊 COMPREHENSIVE ATMOSPHERIC ANALYTICS - UZBEKISTAN (2017-2024)")
    print("=" * 70)
    print("🎯 Analysis parameters:")
    print("   • Time period: 2017-2024 (8 years)")
    print("   • 10 major cities")
    print("   • 3 gases (NO₂, CO, CH₄)")
    print("   • Monthly temporal resolution")
    print("   • Trend analysis & forecasting")
    print("   • Interactive maps & visualizations")
    print("   • Seasonal decomposition")
    print("=" * 70)
    
    try:
        # Initialize GEE
        print("\n🔧 Initializing Google Earth Engine...")
        ee.Initialize(project='ee-sabitovty')
        print("✅ Google Earth Engine initialized")
        
        # Define study area
        uzbekistan_bounds = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        
        # Cities with detailed information
        cities = {
            'Tashkent': {
                'coords': [69.2401, 41.2995],
                'population': 2500000,
                'type': 'Capital',
                'region': 'Tashkent'
            },
            'Samarkand': {
                'coords': [66.9597, 39.6270],
                'population': 520000,
                'type': 'Historic',
                'region': 'Samarkand'
            },
            'Namangan': {
                'coords': [71.6726, 40.9983],
                'population': 480000,
                'type': 'Industrial',
                'region': 'Fergana Valley'
            },
            'Andijan': {
                'coords': [72.3442, 40.7821],
                'population': 450000,
                'type': 'Industrial',
                'region': 'Fergana Valley'
            },
            'Bukhara': {
                'coords': [64.4207, 39.7747],
                'population': 280000,
                'type': 'Historic',
                'region': 'Central'
            },
            'Nukus': {
                'coords': [59.6103, 42.4531],
                'population': 260000,
                'type': 'Regional',
                'region': 'Karakalpakstan'
            },
            'Qarshi': {
                'coords': [65.7887, 38.8569],
                'population': 240000,
                'type': 'Regional',
                'region': 'Kashkadarya'
            },
            'Kokand': {
                'coords': [70.9428, 40.5258],
                'population': 230000,
                'type': 'Historic',
                'region': 'Fergana Valley'
            },
            'Urgench': {
                'coords': [60.6348, 41.5500],
                'population': 150000,
                'type': 'Regional',
                'region': 'Khorezm'
            },
            'Margilan': {
                'coords': [71.7246, 40.4731],
                'population': 140000,
                'type': 'Industrial',
                'region': 'Fergana Valley'
            }
        }
        
        print(f"\n📍 Comprehensive analysis for {len(cities)} cities over 8 years")
        
        # Create city points
        city_features = []
        for city_name, city_info in cities.items():
            coords = city_info['coords']
            feature = ee.Feature(
                ee.Geometry.Point(coords),
                {
                    'city': city_name,
                    'lon': coords[0],
                    'lat': coords[1],
                    'population': city_info['population'],
                    'type': city_info['type'],
                    'region': city_info['region']
                }
            )
            city_features.append(feature)
        
        city_collection = ee.FeatureCollection(city_features)
        
        # Gas datasets
        datasets = {
            'NO2': {
                'collection': 'COPERNICUS/S5P/OFFL/L3_NO2',
                'band': 'tropospheric_NO2_column_number_density',
                'scale': 5000,
                'description': 'Nitrogen Dioxide',
                'unit': 'mol/m²',
                'color': 'red'
            },
            'CO': {
                'collection': 'COPERNICUS/S5P/OFFL/L3_CO',
                'band': 'CO_column_number_density',
                'scale': 5000,
                'description': 'Carbon Monoxide',
                'unit': 'mol/m²',
                'color': 'orange'
            },
            'CH4': {
                'collection': 'COPERNICUS/S5P/OFFL/L3_CH4',
                'band': 'CH4_column_volume_mixing_ratio_dry_air',
                'scale': 5000,
                'description': 'Methane',
                'unit': 'ppb',
                'color': 'green'
            }
        }
        
        # Time series analysis (2017-2024)
        print(f"\n📅 Collecting 8-year time series data...")
        
        all_data = []
        total_months = 12 * 8  # 8 years
        month_count = 0
        
        for year in range(2017, 2025):
            for month in range(1, 13):
                if year == 2024 and month > 8:  # Only up to August 2024
                    break
                
                month_count += 1
                progress = month_count / total_months * 100
                print(f"   📊 Processing {year}-{month:02d} ({progress:.1f}%)")
                
                # Define monthly period
                start_date = f"{year}-{month:02d}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{month+1:02d}-01"
                
                for gas, config in datasets.items():
                    try:
                        # Load monthly data
                        collection = ee.ImageCollection(config['collection']) \
                            .filterDate(start_date, end_date) \
                            .filterBounds(uzbekistan_bounds) \
                            .select(config['band'])
                        
                        size = collection.size().getInfo()
                        
                        if size > 0:
                            # Monthly average
                            monthly_image = collection.mean()
                            
                            # Sample at city locations
                            sampled = monthly_image.sampleRegions(
                                collection=city_collection,
                                scale=config['scale'],
                                projection='EPSG:4326'
                            )
                            
                            # Extract results
                            features = sampled.getInfo()['features']
                            
                            for feature in features:
                                props = feature['properties']
                                concentration = props.get(config['band'])
                                
                                if concentration is not None:
                                    all_data.append({
                                        'date': f"{year}-{month:02d}-15",  # Mid-month
                                        'year': year,
                                        'month': month,
                                        'city': props['city'],
                                        'gas': gas,
                                        'concentration': concentration,
                                        'longitude': props['lon'],
                                        'latitude': props['lat'],
                                        'population': props['population'],
                                        'city_type': props['type'],
                                        'region': props['region'],
                                        'data_points': size
                                    })
                    
                    except Exception as e:
                        print(f"      ⚠️ Warning: {gas} data for {year}-{month:02d}: {str(e)[:50]}...")
        
        print(f"✅ Collected {len(all_data)} data points across 8 years")
        
        # Create comprehensive DataFrame
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        
        if len(df) == 0:
            print("❌ No data collected!")
            return False
        
        print(f"\n📊 Data summary:")
        print(f"   • Total records: {len(df):,}")
        print(f"   • Time range: {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        print(f"   • Cities: {df['city'].nunique()}")
        print(f"   • Gases: {df['gas'].nunique()}")
        
        # Create output directory
        output_dir = Path('outputs/comprehensive_analytics')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw data
        df.to_csv(output_dir / 'time_series_data_2017_2024.csv', index=False)
        print(f"💾 Raw data saved to: {output_dir / 'time_series_data_2017_2024.csv'}")
        
        # Generate visualizations
        print(f"\n🎨 Generating comprehensive visualizations...")
        
        # 1. Time series plots for each gas
        create_time_series_plots(df, datasets, output_dir)
        
        # 2. City comparison plots
        create_city_comparison_plots(df, datasets, cities, output_dir)
        
        # 3. Trend analysis
        create_trend_analysis(df, datasets, output_dir)
        
        # 4. Interactive maps
        create_interactive_maps(df, cities, datasets, output_dir)
        
        # 5. Seasonal analysis
        create_seasonal_analysis(df, datasets, output_dir)
        
        # 6. Regional analysis
        create_regional_analysis(df, datasets, output_dir)
        
        # 7. Statistical summary
        create_statistical_summary(df, datasets, cities, output_dir)
        
        print(f"\n🎉 COMPREHENSIVE ANALYTICS COMPLETE!")
        print(f"📊 Generated visualizations and maps in: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Comprehensive analytics failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_time_series_plots(df, datasets, output_dir):
    """Create time series plots for each gas"""
    print("   📈 Creating time series plots...")
    
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    for i, (gas, config) in enumerate(datasets.items()):
        gas_data = df[df['gas'] == gas]
        
        if len(gas_data) > 0:
            # Group by date and calculate statistics
            monthly_stats = gas_data.groupby('date')['concentration'].agg(['mean', 'std', 'min', 'max']).reset_index()
            
            ax = axes[i]
            ax.plot(monthly_stats['date'], monthly_stats['mean'], 
                   color=config['color'], linewidth=2, label=f'{gas} Mean')
            ax.fill_between(monthly_stats['date'], 
                           monthly_stats['mean'] - monthly_stats['std'],
                           monthly_stats['mean'] + monthly_stats['std'],
                           alpha=0.3, color=config['color'], label=f'{gas} ±1σ')
            
            ax.set_title(f'{config["description"]} Time Series (2017-2024)', fontsize=14, fontweight='bold')
            ax.set_ylabel(f'Concentration ({config["unit"]})')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.xaxis.set_minor_locator(mdates.MonthLocator())
    
    plt.xlabel('Year')
    plt.tight_layout()
    plt.savefig(output_dir / 'time_series_all_gases.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_city_comparison_plots(df, datasets, cities, output_dir):
    """Create city comparison plots"""
    print("   🏙️ Creating city comparison plots...")
    
    for gas, config in datasets.items():
        gas_data = df[df['gas'] == gas]
        
        if len(gas_data) > 0:
            # Calculate city averages
            city_averages = gas_data.groupby('city')['concentration'].agg(['mean', 'std']).reset_index()
            city_averages = city_averages.sort_values('mean', ascending=False)
            
            plt.figure(figsize=(12, 8))
            
            # Bar plot with error bars
            bars = plt.bar(range(len(city_averages)), city_averages['mean'], 
                          yerr=city_averages['std'], capsize=5, 
                          color=config['color'], alpha=0.7)
            
            plt.xticks(range(len(city_averages)), city_averages['city'], rotation=45, ha='right')
            plt.ylabel(f'{config["description"]} ({config["unit"]})')
            plt.title(f'{config["description"]} by City (2017-2024 Average)', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            
            # Add population info
            for i, (bar, city) in enumerate(zip(bars, city_averages['city'])):
                pop = cities[city]['population']
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + city_averages['std'].iloc[i],
                        f'{pop/1000:.0f}K', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            plt.savefig(output_dir / f'{gas}_city_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()

def create_trend_analysis(df, datasets, output_dir):
    """Create trend analysis plots"""
    print("   📊 Creating trend analysis...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    for i, (gas, config) in enumerate(datasets.items()):
        gas_data = df[df['gas'] == gas]
        
        if len(gas_data) > 0:
            # Annual averages
            annual_data = gas_data.groupby('year')['concentration'].agg(['mean', 'std']).reset_index()
            
            # Top subplot for this gas
            row, col = i // 2, i % 2
            if i < 3:  # Only plot if we have space
                ax = axes[row, col] if i < 2 else axes[1, 0]
                
                # Linear trend
                z = np.polyfit(annual_data['year'], annual_data['mean'], 1)
                p = np.poly1d(z)
                
                ax.errorbar(annual_data['year'], annual_data['mean'], 
                           yerr=annual_data['std'], fmt='o', color=config['color'], 
                           capsize=5, label='Annual Mean')
                ax.plot(annual_data['year'], p(annual_data['year']), 
                       '--', color='red', label=f'Trend (slope: {z[0]:.2e}/year)')
                
                ax.set_title(f'{config["description"]} Annual Trend', fontsize=12, fontweight='bold')
                ax.set_ylabel(f'Concentration ({config["unit"]})')
                ax.set_xlabel('Year')
                ax.legend()
                ax.grid(True, alpha=0.3)
    
    # Remove empty subplot
    if len(datasets) == 3:
        fig.delaxes(axes[1, 1])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'trend_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_interactive_maps(df, cities, datasets, output_dir):
    """Create interactive maps"""
    print("   🗺️ Creating interactive maps...")
    
    # Calculate latest year averages for mapping
    latest_year = df['year'].max()
    latest_data = df[df['year'] == latest_year]
    
    for gas, config in datasets.items():
        gas_data = latest_data[latest_data['gas'] == gas]
        
        if len(gas_data) > 0:
            # Create map centered on Uzbekistan
            m = folium.Map(
                location=[41.0, 64.0],
                zoom_start=6,
                tiles='OpenStreetMap'
            )
            
            # Calculate city averages for latest year
            city_averages = gas_data.groupby('city')['concentration'].mean().to_dict()
            
            # Normalize values for color mapping
            values = list(city_averages.values())
            min_val, max_val = min(values), max(values)
            
            for city, city_info in cities.items():
                if city in city_averages:
                    concentration = city_averages[city]
                    
                    # Normalize to 0-1 for color mapping
                    norm_val = (concentration - min_val) / (max_val - min_val) if max_val > min_val else 0
                    
                    # Color from green (low) to red (high)
                    import matplotlib.cm as cm
                    color = cm.RdYlGn_r(norm_val)
                    color_hex = '#%02x%02x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255))
                    
                    folium.CircleMarker(
                        location=city_info['coords'][::-1],  # lat, lon
                        radius=10 + (city_info['population'] / 100000) * 5,  # Size by population
                        popup=f"""
                        <b>{city}</b><br>
                        {config['description']}: {concentration:.2e} {config['unit']}<br>
                        Population: {city_info['population']:,}<br>
                        Type: {city_info['type']}<br>
                        Region: {city_info['region']}
                        """,
                        color='black',
                        fillColor=color_hex,
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(m)
            
            # Add title
            title_html = f'''
                <h3 align="center" style="font-size:16px"><b>{config["description"]} Concentrations - {latest_year}</b></h3>
                '''
            m.get_root().html.add_child(folium.Element(title_html))
            
            # Save map
            m.save(output_dir / f'{gas}_map_{latest_year}.html')

def create_seasonal_analysis(df, datasets, output_dir):
    """Create seasonal analysis plots"""
    print("   🌿 Creating seasonal analysis...")
    
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    for i, (gas, config) in enumerate(datasets.items()):
        gas_data = df[df['gas'] == gas]
        
        if len(gas_data) > 0:
            # Add season column
            gas_data = gas_data.copy()
            gas_data['season'] = gas_data['month'].map({
                12: 'Winter', 1: 'Winter', 2: 'Winter',
                3: 'Spring', 4: 'Spring', 5: 'Spring',
                6: 'Summer', 7: 'Summer', 8: 'Summer',
                9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
            })
            
            # Monthly averages
            monthly_avg = gas_data.groupby('month')['concentration'].mean()
            
            ax = axes[i]
            bars = ax.bar(monthly_avg.index, monthly_avg.values, color=config['color'], alpha=0.7)
            
            ax.set_title(f'{config["description"]} Seasonal Pattern', fontsize=14, fontweight='bold')
            ax.set_ylabel(f'Average Concentration ({config["unit"]})')
            ax.set_xlabel('Month')
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'seasonal_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_regional_analysis(df, datasets, output_dir):
    """Create regional analysis plots"""
    print("   🌍 Creating regional analysis...")
    
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    for i, (gas, config) in enumerate(datasets.items()):
        gas_data = df[df['gas'] == gas]
        
        if len(gas_data) > 0:
            # Regional averages
            regional_avg = gas_data.groupby('region')['concentration'].agg(['mean', 'std']).reset_index()
            regional_avg = regional_avg.sort_values('mean', ascending=False)
            
            ax = axes[i]
            bars = ax.bar(range(len(regional_avg)), regional_avg['mean'], 
                         yerr=regional_avg['std'], capsize=5,
                         color=config['color'], alpha=0.7)
            
            ax.set_title(f'{config["description"]} by Region', fontsize=14, fontweight='bold')
            ax.set_ylabel(f'Average Concentration ({config["unit"]})')
            ax.set_xticks(range(len(regional_avg)))
            ax.set_xticklabels(regional_avg['region'], rotation=45, ha='right')
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'regional_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_statistical_summary(df, datasets, cities, output_dir):
    """Create statistical summary report"""
    print("   📋 Creating statistical summary...")
    
    summary_data = []
    
    for gas, config in datasets.items():
        gas_data = df[df['gas'] == gas]
        
        if len(gas_data) > 0:
            overall_stats = {
                'gas': gas,
                'description': config['description'],
                'unit': config['unit'],
                'total_records': len(gas_data),
                'mean_concentration': gas_data['concentration'].mean(),
                'std_concentration': gas_data['concentration'].std(),
                'min_concentration': gas_data['concentration'].min(),
                'max_concentration': gas_data['concentration'].max(),
                'cities_covered': gas_data['city'].nunique(),
                'years_covered': gas_data['year'].nunique(),
                'months_covered': len(gas_data.groupby(['year', 'month']))
            }
            
            # City with highest/lowest concentrations
            city_avg = gas_data.groupby('city')['concentration'].mean()
            overall_stats['highest_city'] = city_avg.idxmax()
            overall_stats['highest_concentration'] = city_avg.max()
            overall_stats['lowest_city'] = city_avg.idxmin()
            overall_stats['lowest_concentration'] = city_avg.min()
            
            # Trend analysis
            annual_avg = gas_data.groupby('year')['concentration'].mean()
            if len(annual_avg) > 1:
                trend = np.polyfit(annual_avg.index, annual_avg.values, 1)[0]
                overall_stats['annual_trend'] = trend
                overall_stats['trend_direction'] = 'Increasing' if trend > 0 else 'Decreasing'
            else:
                overall_stats['annual_trend'] = 0
                overall_stats['trend_direction'] = 'Insufficient data'
            
            summary_data.append(overall_stats)
    
    # Save statistical summary
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_dir / 'statistical_summary.csv', index=False)
    
    # Create summary report
    with open(output_dir / 'analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE ATMOSPHERIC ANALYSIS REPORT - UZBEKISTAN (2017-2024)\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Data Records: {len(df):,}\n")
        f.write(f"Cities Analyzed: {df['city'].nunique()}\n")
        f.write(f"Gases Analyzed: {df['gas'].nunique()}\n")
        f.write(f"Time Period: {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}\n\n")
        
        for _, row in summary_df.iterrows():
            f.write(f"{row['description']} ({row['gas']}):\n")
            f.write(f"  • Records: {row['total_records']:,}\n")
            f.write(f"  • Mean: {row['mean_concentration']:.2e} {row['unit']}\n")
            f.write(f"  • Range: {row['min_concentration']:.2e} - {row['max_concentration']:.2e} {row['unit']}\n")
            f.write(f"  • Highest: {row['highest_city']} ({row['highest_concentration']:.2e} {row['unit']})\n")
            f.write(f"  • Lowest: {row['lowest_city']} ({row['lowest_concentration']:.2e} {row['unit']})\n")
            f.write(f"  • Trend: {row['trend_direction']} ({row['annual_trend']:.2e}/year)\n\n")

if __name__ == "__main__":
    print("🚀 Starting comprehensive atmospheric analytics (2017-2024)...")
    start_time = time.time()
    
    success = comprehensive_analytics_2017_2024()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️  Analysis completed in {duration:.1f} seconds")
    
    if success:
        print("✅ Comprehensive analytics successful!")
        print("\n📈 Generated outputs:")
        print("   • Multi-year time series plots")
        print("   • City comparison charts")
        print("   • Trend analysis graphs")
        print("   • Interactive concentration maps")
        print("   • Seasonal pattern analysis")
        print("   • Regional comparison plots")
        print("   • Statistical summary reports")
        print("   • Raw time series data (CSV)")
    else:
        print("❌ Comprehensive analytics failed")
