$(document).ready(function () {
    var byLocation = document.querySelector('input[name = "resultsBy"]:checked').id == "beach";
    var beach = document.getElementById("beach-location").value;
    title = "California, US";
    beachLocation ="";
    cityLocation = "";
    countryLocation = "";

    $('.range-slider').jRange({
        from: 2015 ,
        to: 2020,
        scale: [2015,2016,2017,2018,2019,2020],
        isRange :true,
        ondragend :function(){
            range = this.getValue().split(',');
            start_year = range[0];
            end_year = range[1];
            city = document.getElementById("city-l").innerText
            country_code = document.getElementById("country-l").innerText
            update(true, city, country_code, start_year,end_year);
        }

    });
    $('.range-slider').jRange('setValue','2015,2020');


    $(".search").autocomplete({
        minLength: 4,
        source: function (request, response) {
            var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex(request.term), "i");
            response($.grep(data, function (item) {
                return matcher.test(item);
            }));
        }
    });
    $("#organizationsearch").autocomplete({
        minLength: 4,
        source: function (request, response) {
            var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex(request.term), "i");
            response($.grep(orgsearch, function (item) {
                return matcher.test(item);
            }));
        }
    });

    $("#datepicker").datepicker({
        format: "m/d/yyyy",
        startView: "months",
        minViewMode: "months",
        endDate: "+0d",
        startDate: '-6y'
    });

    $("#datepicker1").datepicker({
        format: "mm/dd/yyyy",
        startDate: '-6y'
    });



    onMapHover();
    document.getElementById('scatter').on('plotly_click', function (data) {
        dataHoverInfoBox(data)
    });

});

function dataHoverInfoBox(data){
    //2019-11-23
    //11/23/2019
    eventDate = data.points[0].x;
    e = eventDate.split('-')
    if (e[1][0] =="0"){
        e[1] = e[1][1]
    }
    if (e[2][0] =="0"){
        e[2] = e[2][1]
    }
    eventDate = e[1]+'/'+e[2]+'/'+e[0]
    totalItems= data.points[0].y;
    byLocation = document.querySelector('input[name = "resultsBy"]:checked').id == "beach";
    var params = "date=\'" + eventDate + "\'&totalItems=" + totalItems;
    if (cityLocation.length>0 || beachLocation.length>0) {
        params += "&country_code=" + countryLocation + "&city=" + cityLocation + "&location=\'" + beachLocation
            + "\'&byLocation=" + byLocation;
    }
    var url_name = "/info_box?" + params;
    $.ajax({
        url: url_name,
        data: $('form').serialize(),
        type: 'POST',
        success: function (response) {
            response = JSON.parse(response);
            document.getElementById("organization").href = "https://www.google.com/search?q=" + response[0];
            document.getElementById("organization").innerText = response[0];
            document.getElementById("event-type").innerText = response[2];
            document.getElementById("date-record").innerText = eventDate;
            document.getElementById("total-items-recorded").innerText = response[4];
            document.getElementById("event-location").innerText = response[5];
            document.getElementById("event-location").href = "https://maps.google.com?q=" + response[7]+","+response[6];


            if(response[1].length>0){
                document.getElementById("description").innerText = response[1];
                document.getElementById("description-block").style.display = "block";
            }

        },
        error: function (error) {
        }
    });
    document.getElementById("modal-title").innerText = title;
    $("#infoBox").modal()
}

function showMap(){
    var url_name = "/near_me?";
    //$("#events_near_me").modal();
    $.ajax({
        url: url_name,
        data: $('form').serialize(),
        type: 'POST',
        success: function (response) {
            respnse = JSON.parse(response)
            graphs_1 = JSON.parse(respnse['graph']);
            city = respnse['city'];
            country_code = respnse['country_code'];
            Plotly.deleteTraces('map', 0);
            Plotly.newPlot('map', graphs_1);
            onMapHover();
            //update(true, city, country_code);
        },
        error: function (error) {
        }
    });
}


function onMapHover(){
    document.getElementById('map').on('plotly_hover', function (data) {
        if(data.points[0]["customdata"]) {
            var country = data.points[0]["customdata"][2];
            var city = data.points[0]["customdata"][0];
            var location = data.points[0]["customdata"][5];
            byLocation = document.querySelector('input[name = "resultsBy"]:checked').id == "beach";

        } else {
            var country = "";
            var city= "";
            var location = data.points[0]["hovertext"];
            byLocation = true;
        }
        datepicker = document.getElementById("datepicker").value

        if (city != null && country != null) {
            var graphs_1;
            var graphs_2;
            var response_3;
            var params = "country_code=\'" + country + "\'&city=\'" + city + "\'&location=\'" + location + "\'&byLocation=" + byLocation + "";
            if (datepicker.length > 0) {
                month = datepicker.split("/")[0];
                year = datepicker.split("/")[2];
                params += "&month=\'" + month + "\'"+"&year=\'"+year+"\'";
            }
            var url_name1 = "/predScatter?" + params;
            var url_name3 = "/predStats?" + params;
            var url_name4 = "/get_title?" + params;
            $.ajax({
                url: url_name1,
                data: $('form').serialize(),
                type: 'POST',
                success: function (response) {
                    Plotly.deleteTraces('scatter', 0);
                    graphs_1 = JSON.parse(response);
                    Plotly.newPlot('scatter', graphs_1);
                    document.getElementById('scatter').on('plotly_click', function (data) {
                        dataHoverInfoBox(data);
                    });
                    $.ajax({
                        url: url_name3,
                        data: $('form').serialize(),
                        type: 'POST',
                        success: function (response) {
                            response3 = JSON.parse(response);
                            document.getElementsByClassName("card-text")[0].innerText = response3[0];
                            document.getElementsByClassName("card-text")[1].innerText = response3[1];
                            document.getElementsByClassName("card-text")[2].innerText = response3[2];
                            $.ajax({
                                url: url_name4,
                                data: $('form').serialize(),
                                type: 'POST',
                                success: function (response) {
                                    title = JSON.parse(response)[0];
                                    beachLocation = JSON.parse(response)[1];
                                    cityLocation = JSON.parse(response)[2];
                                    countryLocation =JSON.parse(response)[3];
                                    document.getElementById("beach-l").innerText = beachLocation
                                    document.getElementById("city-l").innerText = cityLocation
                                    document.getElementById("country-l").innerText = countryLocation

                                },
                                error: function (error) {
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
}
function reset(){
    document.getElementById("warning").innerText = ""
    $('.range-slider').jRange('setValue','2015,2020');
    var graphs_1;
    var graphs_2;
    var url_name1 = "/create_scatter";
    var url_name3 = "/get_stats";
    var url_name5 = "/create_map";
    $.ajax({
        url: url_name5,
        data: $('form').serialize(),
        type: 'POST',
        success: function (response) {
            graphs_2 = JSON.parse(response);
            Plotly.deleteTraces('map', 0);
            Plotly.newPlot('map', graphs_2);
            onMapHover()
            $.ajax({
                url: url_name3,
                data: $('form').serialize(),
                type: 'POST',
                success: function (response) {
                    response3 = JSON.parse(response);
                    document.getElementsByClassName("card-text")[0].innerText = response3[0];
                    document.getElementsByClassName("card-text")[1].innerText = response3[1];
                    document.getElementsByClassName("card-text")[2].innerText = response3[2];
                    $.ajax({
                        url: url_name1,
                        data: $('form').serialize(),
                        type: 'POST',
                        success: function (response) {
                            Plotly.deleteTraces('scatter', 0);
                            graphs_1 = JSON.parse(response);
                            Plotly.newPlot('scatter', graphs_1);
                            document.getElementById('scatter').on('plotly_click', function (data) {
                                dataHoverInfoBox(data)
                            });
                        },
                        error: function (error) {
                        }});
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
function update(byName = false, city = null, country_code = null, start_year=null, end_year=null) {
    document.getElementById("warning").innerText = ""
    org= document.getElementById("organizationsearch").value
    if (!byName) {
        city = document.getElementById("city-l").innerText
        country = document.getElementById("country-l").innerText
        beach = document.getElementById("beach-location").value
        datepicker = document.getElementById("datepicker").value
        var params = "";
        if (beach.length > 0)
            byLocation = true;
        else byLocation = false;
        params += "location=\'" + beach + "\'&byLocation=" + byLocation + "";
        if (datepicker.length > 0) {
            month = datepicker.split("/")[0];
            year = datepicker.split("/")[2];
            params += "&month=\'" + month + "\'"+"&year=\'"+year+"\'";
            params += "&city=" + city + "&country_code="+country
        }
    } else {
        var params = "";
        params += "city=" + city + "&byLocation=" + false + "&country_code="+country_code+"";
    }
    if(start_year && end_year){
        params += "&start_year=" + start_year + "&end_year="+end_year;
    }else {
        range = $('.range-slider').jRange('getValue').split(',');
        start_year = range[0];
        end_year = range[1];
        if (start_year && end_year)
            params += "&start_year=" + start_year + "&end_year="+end_year;
    }
    if(org){
        params += "&org=" + org;
    }
    var mapby = document.getElementById("itemscollected").checked
    if(mapby){
        params += "&mapby=" + true;
    }
    var graphs_1;
    var graphs_2;
    var url_name1 = "/create_scatter?" + params;
    var url_name3 = "/get_stats?" + params;
    var url_name5 = "/create_map?" + params;
    $.ajax({
        url: url_name5,
        data: $('form').serialize(),
        type: 'POST',
        success: function (response) {
            graphs_2 = JSON.parse(response);
            Plotly.deleteTraces('map', 0);
            Plotly.newPlot('map', graphs_2);
            onMapHover()
            $.ajax({
                url: url_name3,
                data: $('form').serialize(),
                type: 'POST',
                success: function (response) {
                    response3 = JSON.parse(response);
                    if (response3[0] && response3[0].length <= 0)
                        response3[0] = "No information"
                    document.getElementsByClassName("card-text")[0].innerText = response3[0];
                    document.getElementsByClassName("card-text")[1].innerText = response3[1];
                    document.getElementsByClassName("card-text")[2].innerText = response3[2];
                    $.ajax({
                        url: url_name1,
                        data: $('form').serialize(),
                        type: 'POST',
                        success: function (response) {
                            Plotly.deleteTraces('scatter', 0);
                            graphs_1 = JSON.parse(response);
                            Plotly.newPlot('scatter', graphs_1);
                            document.getElementById('scatter').on('plotly_click', function (data) {
                                dataHoverInfoBox(data)
                            });
                        },
                        error: function (error) {
                        }});
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