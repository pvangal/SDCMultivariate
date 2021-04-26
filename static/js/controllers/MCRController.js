app.controller('MCRController', ['$scope', '$http', function($scope, $http) {
    $scope.isProgressBarVisible = false;
    $scope.layout = {
        autosize: true,
        width: 'auto',
        height: 500,
        xaxis: {
            rangeslider: true
        },
        yaxis: {
            rangeslider: true
        }
    };
    $scope.submit = function() {
        $scope.isProgressBarVisible = true;
        $http({
            url: '/compute_mcr',
            data: $scope.ncomponents,
            method: 'POST',
            headers: {
                'Content-Type': undefined,
            }}).then(function(response) {
                $scope.isProgressBarVisible = false;
                $scope.plotlydataConcentrations = [];
                for (var i = 0; i< response.data['concentration'].length; i++){
                    $scope.plotlydataConcentrations.push({
                        y: response.data['concentration'][i],
                        x: response.data['timestamps'],
                        type: 'line',
                    });
                }
                $scope.plotlydataComponents = [];
                for (var i = 0; i< response.data['spectra'].length; i++){
                    $scope.plotlydataComponents.push({
                        y: response.data['spectra'][i],
                        x: response.data['wavelengths'],
                        type: 'line',
                    });
                }
            }, function(response) {
                $scope.isProgressBarVisible = false;
                $scope.plotlydata = null
            });
    };

    
}])