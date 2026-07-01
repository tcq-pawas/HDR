// This file is now empty - all React code has been moved to dashboard.html
<div className="min-h-screen bg-slate-50 flex">

    {/* Sidebar */}
    <Sidebar />

    {/* Main Content */}
    <div className="flex-1 ml-[220px] p-6">

        <PageHeader />

        <HeroBanner />

        <StatsCards />

        <div className="grid grid-cols-12 gap-6 mt-6">

            <div className="col-span-8">
                <PortfolioGrowth />
            </div>

            <div className="col-span-4">
                <ROISummary />
            </div>

        </div>

        <div className="grid grid-cols-12 gap-6 mt-6">

            <div className="col-span-8">
                <RecentInvestments />
            </div>

            <div className="col-span-4">
                <InvestmentDistribution />
            </div>

        </div>

        <div className="grid grid-cols-12 gap-6 mt-6">

            <div className="col-span-8">
                <RecommendedOpportunities />
            </div>

            <div className="col-span-4">
                <MarketUpdates />
                <Notifications />
            </div>

        </div>

        <QuickActions />

    </div>

</div>