app.controller('SpectrumController', [$scope, function($scope) {
    $scope.plotlylayout = {
        showlegend: true,
        height: 600,
        margin: {
            l: 50,
            r: 50,
            t: 50,
            b: 50
        },
        xaxis: {
            autorange: true,
            rangeslider: {},
        }
        yaxis: {
            autorange: true,
            type: linear
        } 
    }
    function preparePlot(data) {
        $scope.plotlydata = [];
        $scope.plotlydata.push({
            mode: 'surface',
            z: data,
            
        })
    }
}]