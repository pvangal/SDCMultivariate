app.controller('SpectrumController', ['$scope', '$http', function($scope, $http) {
    $scope.isProgressBarVisible = false;
    $scope.layout = {
        autosize: true,
        scene: {
            aspectratio: {
                x: 2,
                y: 1,
                z: 1
            },
            xaxis: {
                range: []
                },
            yaxis: {
                range: []
                }
            },
        
      
    };
    
    $scope.submit = function() {
        $scope.isProgressBarVisible = true;
        fd = new FormData ();
        for (var i = 0; i < $scope.files.length; i++){
            fd.append('file', $scope.files[i]);}
        
        $http({
            method: 'POST',
            url: '/get_spectral_data',
            data: fd,
            headers: {
                'Content-Type': undefined 
            }
        }).then(function(response) {
            $scope.isProgressBarVisible = false;
            $scope.plotlydata = [{
                z: response.data['data'],
                x: response.data['wavelengths'],
                y: response.data['timestamps'],
                colorscale: 'Portland',
                type: 'surface',
                showscale: false,
            }]},
        function(response) {
            $scope.isProgressBarVisible = false;
            $scope.plotlydata = null;
        });   
    };    

    $scope.update_wavelengths = function() {
        var wavelength_url = '/update_wavelength/?wavelength_low=' + $scope.wavelength_low + '&wavelength_high=' + $scope.wavelength_high;
        $http({
            method: 'GET',
            url: wavelength_url,
        }).then(function(response) {
            $scope.layout['scene']['xaxis']['range'] = [$scope.wavelength_low, $scope.wavelength_high];
        },
        function(response) {
            console.log('Could not update');
        });
        
    };

    $scope.update_time = function() {
        var time_url = '/update_time/?time_low=' + $scope.time_low + '&time_high=' + $scope.time_high;
        $http({
            method: 'GET',
            url: time_url,
        }).then(function(response) {
            $scope.layout['scene']['yaxis']['range'] = [$scope.time_low, $scope.time_high]
        },
        function(response) {
            console.log('Could not update');
        });  
    };
    
}]);