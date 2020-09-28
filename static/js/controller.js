$(document).ready(function () {
    var byLocation = document.querySelector('input[name = "resultsBy"]:checked').id == "beach";
    var beach = document.getElementById("beach-location").value;
    $(".search").autocomplete({
        minLength: 4,
        source: function (request, response) {
            var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex(request.term), "i");
            response($.grep(data, function (item) {
                return matcher.test(item);
            }));
        }
    });
    $("#datepicker").datepicker({
        format: "yyyy/mm",
        startView: "months",
        minViewMode: "months",
        endDate: "+0d",
        startDate: '-6y'
    });

    function update() {
        document.getElementById("warning").innerText = ""
        beach = document.getElementById("beach-location").value
        datepicker = document.getElementById("datepicker").value
        var params = "";
        if (beach.length == 0 && datepicker.length == 0)
            return;
        if (beach.length > 0)
            byLocation = true;
        params += "location=\'" + beach + "\'&byLocation=" + byLocation + "";
        if (datepicker.length > 0)
            params += "&month_year=\'" + datepicker + "\'";
        var graphs_1;
        var graphs_2;
        var url_name1 = "/create_scatter?" + params;
        var url_name2 = "/create_plot?" + params;
        var url_name3 = "/get_stats?" + params;
        $.ajax({
            url: url_name1,
            data: $('form').serialize(),
            type: 'POST',
            success: function (response) {
                Plotly.deleteTraces('scatter', 0);
                graphs_1 = JSON.parse(response);
                Plotly.newPlot('scatter', graphs_1);
                $.ajax({
                    url: url_name2,
                    data: $('form').serialize(),
                    type: 'POST',
                    success: function (response) {
                        graphs_2 = JSON.parse(response);
                        Plotly.deleteTraces('bar', 0);
                        Plotly.newPlot('bar', graphs_2);
                        $.ajax({
                            url: url_name3,
                            data: $('form').serialize(),
                            type: 'POST',
                            success: function (response) {
                                response3 = JSON.parse(response);
                                document.getElementsByClassName("card-text")[1].innerText = response3[0];
                                document.getElementsByClassName("card-text")[2].innerText = response3[1];
                                document.getElementsByClassName("card-text")[3].innerText = response3[2];
                                document.getElementsByClassName("card-text")[4].innerText = response3[3];
                            },
                            error: function (error) {
                                document.getElementById("warning").innerText = "No results for the entered filters";
                            }
                        });

                    },
                    error: function (error) {
                        document.getElementById("warning").innerText = "No results for the entered filters";
                    }
                });
            },
            error: function (error) {
                document.getElementById("warning").innerText = "No results for the entered filters";
            }
        });
    }

    document.getElementById('map').on('plotly_hover', function (data) {
        var country = data.points[0]["customdata"][2];
        var city = data.points[0]["customdata"][0];
        var location = data.points[0]["customdata"][5];
        byLocation = document.querySelector('input[name = "resultsBy"]:checked').id == "beach";
        console.log(byLocation);
        if (city != null && country != null) {
            var graphs_1;
            var graphs_2;
            var response_3;
            var params = "country_code=\'" + country + "\'&city=\'" + city + "\'&location=\'" + location + "\'&byLocation=" + byLocation + "";
            var url_name1 = "/create_scatter?" + params;
            var url_name2 = "/create_plot?" + params;
            var url_name3 = "/get_stats?" + params;

            $.ajax({
                url: url_name1,
                data: $('form').serialize(),
                type: 'POST',
                success: function (response) {
                    Plotly.deleteTraces('scatter', 0);
                    graphs_1 = JSON.parse(response);
                    Plotly.newPlot('scatter', graphs_1);
                    document.getElementById('scatter').on('plotly_click', function (data) {
                    });
                    $.ajax({
                        url: url_name2,
                        data: $('form').serialize(),
                        type: 'POST',
                        success: function (response) {
                            graphs_2 = JSON.parse(response);
                            Plotly.deleteTraces('bar', 0);
                            Plotly.newPlot('bar', graphs_2);
                            $.ajax({
                                url: url_name3,
                                data: $('form').serialize(),
                                type: 'POST',
                                success: function (response) {
                                    response3 = JSON.parse(response);
                                    document.getElementsByClassName("card-text")[1].innerText = response3[0];
                                    document.getElementsByClassName("card-text")[2].innerText = response3[1];
                                    document.getElementsByClassName("card-text")[3].innerText = response3[2];
                                    document.getElementsByClassName("card-text")[4].innerText = response3[3];
                                },
                                error: function (error) {
                                    console.log(error);
                                }
                            });

                        },
                        error: function (error) {
                            console.log(error);
                        }
                    });
                },
                error: function (error) {
                    console.log(error);
                }
            });
        }
    });
    document.getElementById('scatter').on('plotly_click', function (data) {
    });

});