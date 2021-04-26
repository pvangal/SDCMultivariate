app.directive('fileModel', ['$parse', function($parse) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var model = $parse(attrs.fileModel);
            var modelSetter = model.assign;
            element.bind('change', function() {
                filelist = [];
                scope.$apply(function() {
                    for (var i = 0; i < element[0].files.length; i++) {
                        filelist.push(element[0].files[i]);
                    }
                    modelSetter(scope, filelist);
                });
            });
        }
    };
}]);