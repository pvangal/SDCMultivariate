app.controller('PCAController', ['$scope', '$http', function($scope, $http) {
    $scope.layout = {
        autosize: true,
        width: 'auto',
        height: 500,
    };

    $scope.submit = function() {
        $scope.explainedVariance = [];
        $http({
            method: 'POST',
            url: '/compute_pca',
            data: $scope.ncomponents,
            headers: {
                'Content-Type': undefined 
            }
        }).then(function(response) {
            $scope.plotlydata = [{
                y: response.data['variance'],
                x: response.data['index'],
                type: 'line',
            }];
            for(var i = 0; i < response.data['index'].length; i++){
                $scope.explainedVariance.push([response.data['index'][i], response.data['variance'][i]]);
            }
        },
        function(response) {
            $scope.plotlydata = null;
        });
    };
}])